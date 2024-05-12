

readParm <- function(FileName) {
  wd1 <- c(8, 8)
  PARM1 <- read.fwf(FileName, widths = wd1, n = 30)
  VarNames1 <- c(paste0("SCRP1_", c(1:30)), paste0("SCRP2_", c(1:30)))
  PARM1_1 <- t(data.frame("parm" = c(PARM1[, 1], PARM1[, 2])))
  colnames(PARM1_1) <- VarNames1
  wd2 <- c(rep(8, 10))
  PARM2 <- read.fwf(FileName, widths = wd2, skip = 30, n = 13)
  PARM3 <- c()
  for (ii in 1:nrow(PARM2)) {
    PARM3 <- c(PARM3, as.numeric(unlist(PARM2[ii, ])))
  }
  PARM4 <- PARM3[!is.na(PARM3)]
  # PARM4<-PARM3
  PARM5 <- t(data.frame("parm" = PARM4))
  colnames(PARM5) <- paste0("PARM", c(1:length(PARM4)))
  return(cbind(PARM1_1, PARM5))
}



writeParm <- function(x, FileName) {
  # num.decimals <- function(xpp) {
  #   xp<-round(xpp, digits = 2)
  #   stopifnot(class(xp)=="numeric")
  #   xp <- sub("0+$","",xp)
  #   xp <- sub("^.+[.]","",xp)
  #   nchar(xp)
  # }

  options(scipen = 999)

  nDigits <- function(x) nchar(trunc(abs(x)))

  decimalplaces <- function(x) {
    if ((x %% 1) != 0) {
      nchar(strsplit(sub("0+$", "", as.character(x)), ".", fixed = TRUE)[[1]][[2]])
    } else {
      return(0)
    }
  }

  x1 <- data.frame("s1" = x[, 1:30], "s2" = x[, 31:60])
  textFormat1 <- "%8.2f%8.2f"
  text1 <- c()
  for (ii in 1:nrow(x1)) {
    if (sum(is.na(x1[ii, ]) == 0)) {
      text1 <- c(text1, do.call("sprintf", c(textFormat1, x1[ii, ])))
    } else {
      text1 <- c(text1, " ")
    }
  }
  x2 <- x[, 61:length(x)]

  # x3 <- data.frame("value" = c(
  #   x2[1:79], NA, x2[80:94], rep(NA, 5),
  #   x2[95:99], rep(NA, 5), x2[100:103],
  #   rep(NA, 6)
  # ))


  x3 <- data.frame("value" = c(
    x2[1:103], rep(NA, 7),
    x2[104:108], rep(NA, 5), x2[109:112],
    rep(NA, 6)
  ))


  # x3<-data.frame('value'=c(x2[1:98], NA, NA, x2[99:103], rep(NA, 5),
  #                          x2[104:107], rep(NA, 6)))
  # textFormat2<-rep('%8.2f', 10)
  text2 <- c()
  iid <- 0
  for (ii in 1:13) {
    text3 <- c()
    for (jj in 1:10) {
      iid <- iid + 1
      if (is.na(x3[iid, 1])) {
        text3 <- paste0(text3, "")
      } else {
        if (nDigits(x3[iid, 1]) == 1) {
          if (decimalplaces(x3[iid, 1]) <= 2) {
            textFormat2 <- "%8.2f"
          } else if (decimalplaces(x3[iid, 1]) > 6) {
            textFormat2 <- "%8.6f"
          } else {
            textFormat2 <- paste0("%8.", decimalplaces(x3[iid, 1]), "f")
            # textFormat2<-'%8.2f'
          }
        } else {
          textFormat2 <- "%8.2f"
        }

        text3 <- paste0(text3, sprintf(textFormat2, x3[iid, 1]))
      }
    }
    text2 <- c(text2, text3)
  }
  text <- c(text1, text2)
  options(scipen = 0)

  con <- file(FileName, open = "w")
  writeLines(text, con)
  close(con)
}