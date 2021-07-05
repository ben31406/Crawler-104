# Crawler-104

協助爬取104人力銀行網站上特定公司的所有職缺中含有某些關鍵字的資訊。

指定公司名稱及關鍵字list，程式將輸出一個Excel檔案，該檔案中儲存指定公司於104人力銀行網站上含有指定關鍵字的職缺資訊，包含"職位名稱"、"工作地點"、"薪資"、"更新時間"、"關鍵字"、"網址"
(備註：關鍵字搜尋範圍包含職缺名稱與職缺內容說明)

# 使用說明：
Step.1 下載requirements.txt，於終端機執行 "pip install -r requirements.txt"\
Step.2 在setting.py中修改JOB_KEY，將所有關鍵字以list方式儲存\
Step.3 在setting.py中修改SAVE_PATH，指定Excel檔案輸出路徑\
Step.4 於終端機執行main.py (Example：python main.py -c 國泰)
