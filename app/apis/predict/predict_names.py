



def filename_to_predictname(filename:str) -> str:
  #remove extension
  predict_name = filename.split('.')[0]
  return predict_name