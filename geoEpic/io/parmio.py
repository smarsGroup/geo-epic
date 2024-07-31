import pandas as pd
import numpy as np
from rpy2.robjects import r, pandas2ri
pandas2ri.activate()
import os

script = '''readParm <- function(FileName) {
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
}'''

r(script)

class CropCom:
    
    def __init__(self, path):
        """
        Load data from a file into DataFrame.
        """
        wd = [5, 5] + [8] * 58 + [50]
        if not path.endswith('.DAT'): 
          path = os.path.join(path, 'CROPCOM.DAT')
        self.data = pd.read_fwf(path, widths=wd, skiprows=1)
        with open(path, 'r') as file:
            self.header = [file.readline() for _ in range(2)]
        self.name = 'CROPCOM'
        self.prms = None
        self.split_columns = ['DLAP1', 'DLAP2', 'WAC2', 'PPLP1', 'PPLP2']
        self.original_columns = self.data.columns.tolist()
        
        # Split the specified columns
        self.split_integer_decimal()

    def split_integer_decimal(self):
        for col in self.split_columns:
            int_col = col + '_v1'
            dec_col = col + '_v2'
            self.data[int_col] = np.floor(self.data[col])
            self.data[dec_col] = (self.data[col] - self.data[int_col])*100
            int_idx = self.data.columns.get_loc(col)
            self.data.insert(int_idx + 1, dec_col, self.data.pop(dec_col))
            self.data.insert(int_idx + 1, int_col, self.data.pop(int_col))

    def combine_integer_decimal(self):
        data = self.data.copy()
        for col in self.split_columns:
            int_col = col + '_v1'
            dec_col = col + '_v2'
            data[col] = data[int_col].astype(int) + data[dec_col]/100
            data.drop(columns=[int_col, dec_col], inplace=True)
        data = data[self.original_columns]
        return data

    @property
    def current(self):
        cols = self.prms['Parm'].values
        all_values = []
        for crop in self.crops:
            crop_values = self.data.loc[self.data['#'] == crop, cols].values.flatten()
            all_values.append(crop_values)
        concatenated_values = np.concatenate(all_values)
        return concatenated_values

    def save(self, path):
        """
        Save DataFrame into an OPC file.
        """
        data = self.combine_integer_decimal()
        if not path.endswith('.DAT'): 
          path = os.path.join(path, 'CROPCOM.DAT')
        with open(path, 'w') as ofile:
            ofile.write(''.join(self.header))
            fmt = '%5d%5s' + '%8.2f'*11 + '%8.4f' + \
              '%8.2f'*5 + '%8.4f'*3 + '%8.2f'*6 + '%8.4f'*9 + \
              '%8.3f'*3 + '%8d' + '%8.2f'*18 + '%8.3f' + '  %s'
            np.savetxt(ofile, data.values, fmt = fmt)
    
    def edit(self, values):
        cols = self.prms['Parm'].values
        values_split = np.split(values, self.split[:-1])
        for i, id in enumerate(self.crops):
            self.data.loc[self.data['#'] == id, cols] = values_split[i]

    def set_sensitive(self, df_paths, crops):
        prms = pd.read_csv(df_paths[0])
        prms['Select'] = prms['Select'].astype(bool)
        for sl in df_paths[1:]:
            df_temp = pd.read_csv(sl)
            prms['Select'] |= df_temp['Select'].astype(bool)
        prms = prms[prms['Select'] == 1]
        prms['Range'] = prms.apply(lambda x: (x['Min'], x['Max']), axis = 1)
        self.prms = prms.copy()
        self.crops = crops
        self.split = np.cumsum([len(self.prms)]*len(crops))
    
    def constraints(self):
        return list(self.prms['Range'].values)*len(self.crops)



class ieParm:

    _metadata = ['header', 'name', 'prms', 'split']

    def __init__(self, path):
        """
        Load data from an ieParm file into DataFrame.
        """
        if not path.endswith('.DAT'): 
          path = os.path.join(path, 'ieParm.DAT')
        df = r['readParm'](path)
        df = pd.DataFrame(df)
        df.columns = ["SCRP1_" + str(i) for i in range(1, 31)] + \
                     ["SCRP2_" + str(i) for i in range(1, 31)] + \
                     ["PARM" + str(i) for i in range(1, 113)]
        
        self.data = df
        self.name = 'ieParm'
        self.prms = None


    def save(self, path):
        if not path.endswith('.DAT'): 
          path = os.path.join(path, 'ieParm.DAT')
        r['writeParm'](self.data.values, path)
    
    def edit(self, values):
        cols = self.prms['Parm'].values
        self.data.loc[0, cols] = values
        
    @property
    def current(self):
        cols = self.prms['Parm'].values
        return self.data.loc[0, cols]

    def set_sensitive(self, df_paths):
        prms = pd.read_csv(df_paths[0])
        for sl in df_paths[1:]:
            df_temp = pd.read_csv(sl)
            prms['Select'] |= df_temp['Select']
        prms = prms[prms['Select'] == 1]
        prms['Range'] = prms.apply(lambda x: (x['Min'], x['Max']), axis = 1)
        self.prms = prms.copy()
        
    def constraints(self):
        return list(self.prms['Range'].values)



