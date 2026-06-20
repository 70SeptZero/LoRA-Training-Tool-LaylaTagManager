import chardet
def detect_encoding(file_path):
   with open(file_path, 'rb') as f:
       data = f.read()
       result = chardet.detect(data)
       encoding = result['encoding']
       print(f"CSV文件的编码格式为：{encoding}")
file_path = 'tags.csv'
detect_encoding(file_path)