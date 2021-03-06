cleanDT <- function(DT) {
  DT$date <- ymd(DT$date)
  DT$updated_on <- ymd_hms(DT$updated_on, tz = "Europe/Berlin")
  DT$value <- as.numeric(DT$value)
  DT <- DT[!is.na(value)]
  DT <- DT[!is.na(key)]

  DT <- unique(DT, by = c("date", "country", "key", "updated_on"))
  DT <- DT[date <= Sys.Date()]
  DT <- DT[order(updated_on)]

  DT <- DT[, .SD[.N], by = c("date", "key", "country")]
  DT <- DT[order(date)]

  return(DT)
}


patch <- function(DT.original, DT.patches) {
  # combine patches with original data :
  print("combine patches with original data...")
  
  # we set the order of priority to avoid that newly retrieve data (DT.original) do not override the patches.
  DT.patches$priority <- 2
  DT.original$priority <- 1
  
  

  DT.with.patches <- rbindlist(list(DT.original, DT.patches), fill = TRUE)
  
  
  print(" finished combine patches with original data...")
  # filter on latest updated_on :
  print("filter on latest updated_on...")
  setkey(DT.with.patches, country, key, date)
  DT.with.patches <- DT.with.patches[order(priority,updated_on)]
 
  DT.with.patches.latest <- DT.with.patches[, .SD[.N], by = c("date", "key", "country")]

  print("finished filter on latest updated_on.")

  saveDTtoS3(DT.with.patches.latest[, c("country", "date", "key", "value", "updated_on", "source_url", "filename")], "all_EU_patched.csv.gz")
  #DT.with.patches.latest[country=="DK" & key=="cases" & date=="2020-05-23"]
  return(DT.with.patches.latest)
}

getListOfPatches <- function() {
  list.files <- get_bucket_df(
    key = AWS_ACCESS_KEY_ID,
    secret = AWS_SECRET_ACCESS_KEY, bucket = "checkercovid",max=Inf 
  )

  setDT(list.files)
  print("finished retrieving list of s3 files.")
  patch.files <- list.files[startsWith(Key, "patch_") & Size > 0]
  patch.files <- paste0(ROOT_S3, patch.files$Key)

  return(patch.files)
}

combinePatches <-  function(patch.files){
    print("reading list of s3 patches files...")
    DT.patches <- rbindlist(lapply(patch.files, fread))
    print("finished reading list of s3 patches files...")
    DT.patches[, date := ymd(date)]
    DT.patches[, updated_on := as_datetime(updated_on)]
    
    return (DT.patches)
}
  
patchAllData <- function() {
  DT.original <- fread(paste0(ROOT_S3, "all_EU.csv.gz"))

  DT.original <- cleanDT(DT.original)
  print("retrieve list of s3 files...")
  patch.files <- getListOfPatches()
  
  
  if (length(patch.files) > 0) {
    DT.patches <-  combinePatches(patch.files)
    DT.with.patches.latest <- patch(DT.original, DT.patches)
    print("saving all_EU_patched.csv.gz to S3...")
    saveDTtoS3(DT.with.patches.latest, "all_EU_patched.csv.gz")
    
    return(DT.with.patches.latest)
  } else {
    return(DT.original)
  }
}

patchSingle <- function(DT.original, DT.patches) {
  DT.patches[, date := ymd(date)]

  DT.patches[, updated_on := as_datetime(updated_on, tz = "Europe/Berlin")]
  DT.with.patches <- patch(DT.original, DT.patches)

  return(DT.with.patches)
}
