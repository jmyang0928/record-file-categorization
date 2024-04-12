#!/usr/bin/env python
# coding: utf-8

# ## Read json files

# In[ ]:


import json

try:
	# 讀取課程時間對照檔案
	with open("const/class_time.json", "r", encoding="utf-8") as file:
		classTime = json.load(file)

	# 讀取課堂名稱對照檔案
	with open("const/class_id.json", "r", encoding="utf-8") as file:
		classID = json.load(file)

	# 讀取存放路徑檔案
	with open("const/paths.json", "r", encoding="utf-8") as file:
		my_paths = json.load(file)

	# 讀取硬體資訊檔案
	with open("const/hardware_info.json", "r") as file:
		hardwareInfo = json.load(file)
  
except FileNotFoundError as e:
  print("[ERROR]", e)


# ## Init log

# In[ ]:


import time
import logging
import os
from os import path

# 宣告 Log 存放位置
log_dir = path.join(my_paths['root_path'], my_paths['backup_path'], my_paths['log_dir'])

# 建立 Log 檔案
log_index = 1
while path.exists(path.join(log_dir, f"{time.strftime("%Y%m%d", time.localtime())}_{log_index}.log")):
    log_index += 1
log_path = path.join(log_dir, f"{time.strftime("%Y%m%d", time.localtime())}_{log_index}.log")

try:
    os.makedirs(log_dir)
except FileExistsError:
    pass
except Exception as e:
    print(f"Making directory fail: {e}")

print(f"! Log file at {log_path}")

# 初始化 Log
logging.basicConfig(filename=log_path, level=logging.INFO, encoding="utf-8", format="%(asctime)s: [%(levelname)s]: %(message)s")
logging.info(f"{"="*20} Program Start {"="*20}")


# ## Find disk

# In[ ]:


# 載入硬體資訊
SerialNo = hardwareInfo['SerialNo']
found_disk = False

# 尋找硬體路徑
for disk in range(ord('E'), ord('Z') + 1):
    model_path = path.join((f"{chr(disk)}:/"), "MODEL.txt")
    if not os.path.exists(model_path):
        continue

	# 讀取硬體資訊
    model_file = open(model_path, 'r')
    context = model_file.read()
    model_file.close()
    try:
        index = context.index("Serial No.:")
        if int(context[context.index("Serial No.:")+11:]) != (SerialNo):
            print(f"X [ERROR] MODEL.txt found, but Serial Number not matched.")
            logging.error(f"MODEL.txt found, but Serial Number not matched.")
            continue
    except ValueError:
        print(f"X [ERROR] MODEL.txt found, but Serial Number not exist.")
        logging.error(f"MODEL.txt found, but Serial Number not exist.")
        continue

	# 硬體資訊匹配
    found_disk = True
    print(f"O Plaud Note found at {chr(disk)}:/, Serial Number matched.")
    logging.info(f"Plaud Note found at {chr(disk)}:/, Serial Number matched.")
    break

# 若未連接硬體，程式結束
if not found_disk:
    print(f"XPlaud Note not found.")
    logging.error(f"XPlaud Note not found.")
    raise SystemExit

plaud_path = chr(disk)+":/"


# ## Log Tree

# In[ ]:


import subprocess

# Log 紀錄原始檔案樹狀結構
command = f"tree {plaud_path} /A /F"
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
output, error = process.communicate()

if error:
    print(error)
else:
    decoded_output = output.decode('utf-8').replace("\r\n", "\n")
    logging.info(f"================= Log Tree Start =================\n{decoded_output}\n=================  Log Tree End  =================")


# ## Count all files

# In[ ]:


# 計算總檔案數量，用於計算執行進度和預估完成時間
total_files = 0
for root, directories, files in os.walk(plaud_path):
    for file in files:
        if not file.startswith('.'):
            if file.endswith(".ASR") or file.endswith("WAV"):
                total_files += 1


# ## Utility
# * Calc audio length
# * Calc md5 sum

# In[14]:


# 計算檔案音訊時長，用於更準確歸類課程
import wave

def get_audio_length(audio_path):
	audio_file = wave.open(audio_path, "rb")
	frame_rate = audio_file.getframerate()
	n_frames = audio_file.getnframes()
	audio_file.close()
	return n_frames / frame_rate


# 計算檔案 MD5 sum，用於確認檔案複製結果
import hashlib

def get_md5(filename):
	with open(filename, "rb") as f:
		md5_hash = hashlib.md5()
		for chunk in iter(lambda: f.read(4096), b""):
			md5_hash.update(chunk)
		calculated_md5 = md5_hash.hexdigest()
	return calculated_md5


# ## Triverse files

# In[ ]:


import shutil
from os import listdir
from datetime import datetime

# 走訪所有檔案，複製搬移
progress = 0
fail_files = []
success_files = []
start_time = datetime.now()
backup_path = path.join(my_paths['root_path'], my_paths['backup_path'])

# 搬移通話錄音檔案
calls_dir = path.join(plaud_path, "CALLS")
if path.exists(calls_dir):
	# 走訪所有資料夾
	for record_dir in listdir(calls_dir):
		date_obj = datetime.strptime(record_dir, "%Y%m%d")
		raw_dest_dir = path.join(backup_path, "raw", "CALLS", record_dir)
		transfered_dest_dir = path.join(backup_path, "transfered", f"{record_dir}_{date_obj.strftime("%a")}_calls")

		# 建立目的地資料夾
		try:
			os.makedirs(raw_dest_dir)
		except FileExistsError:
			pass
		except Exception as e:
			print(f"Making directory fail: {e}")
			logging.error(f"Making directory fail: {e}")
		try:
			os.makedirs(transfered_dest_dir)
		except FileExistsError:
			pass
		except Exception as e:
			print(f"Making directory fail: {e}")
			logging.error(f"Making directory fail: {e}")

		# 走訪資料夾內檔案
		for reocrd_files in listdir(path.join(calls_dir, record_dir)):
			raw_file = path.join(calls_dir, record_dir, reocrd_files)
			datetime_obj = datetime.fromtimestamp(int(reocrd_files[:10]))
			record_file_mane = datetime_obj.strftime("%Y%m%d_%a_%H%M%S") + reocrd_files[10:]

			# 複製檔案
			try:
				backup_raw_file = path.join(raw_dest_dir, reocrd_files)
				shutil.copy2(raw_file, backup_raw_file)
				logging.info(f"backup success from {raw_file} to {backup_raw_file}")
			except Exception as e:
				print(f"Error copying file: {e}")
				logging.error(f"Error copying file: {e}")
			try:
				backup_transfered_file = path.join(transfered_dest_dir, record_file_mane)
				shutil.copy2(raw_file, backup_transfered_file)
				logging.info(f"backup success from {raw_file} to {backup_transfered_file}")
			except Exception as e:
				print(f"Error copying file: {e}")
				logging.error(f"Error copying file: {e}")

			if reocrd_files[10:] == ".WAV":
				has_category = True
				destination_dir = path.join(backup_path, "CALLS", date_obj.strftime("%Y%m%d_%a"))
				try:
					os.makedirs(destination_dir)
				except FileExistsError:
					pass
				except Exception as e:
					print(f"Making directory fail: {e}")
					logging.error(f"Making directory fail: {e}")

				try:
					category_file = path.join(destination_dir, f"{datetime_obj.strftime("%Y%m%d_%a_%H%M%S")}.WAV")
					shutil.copy2(raw_file, category_file)
					logging.info(f"category success from {raw_file} to {category_file}")
				except Exception as e:
					print(f"Error copying file: {e}")
					logging.error(f"Error copying file: {e}")
			else:
				has_category = False

			# 檢測複製結果是否成功
			original_md5 = get_md5(raw_file)
			check_raw_md5 = (path.exists(backup_raw_file) and  original_md5 == get_md5(backup_raw_file))
			check_transfered_md5 = (path.exists(backup_transfered_file) and original_md5 == get_md5(backup_transfered_file))
			check_category_md5 = (not has_category) or (path.exists(category_file) and original_md5 == get_md5(category_file))
			check_total_md5 = check_raw_md5 and check_transfered_md5 and check_category_md5
			if check_total_md5:
				success_files.append(raw_file)
			else:
				fail_files.append(raw_file)

			print(f"{"O" if check_total_md5 else "X"} {raw_file}")
			print("\t=>", f"{"O" if check_raw_md5 else "X"}", backup_raw_file)
			print("\t=>", f"{"O" if check_transfered_md5 else "X"}", backup_transfered_file)
			if has_category:
				print("\t=>", f"{"O" if check_category_md5 else "X"}", category_file)
			logging.info(f"{progress:{len(str(total_files))}d}/{total_files} ({progress*100//total_files:3d}%) [{"="*(progress*100//total_files)}>{" "*(99 - progress*100//total_files)}]")
			logging.info(f"{raw_file}...")
			logging.info(f"\t\t=> {"O" if check_raw_md5 else "X"} {backup_raw_file}")
			logging.info(f"\t\t=> {"O" if check_transfered_md5 else "X"} {backup_transfered_file}")
			if has_category:
				logging.info(f"\t\t=> {"O" if check_category_md5 else "X"} {category_file}")

			# 計算預估完成時間
			progress += 1
			delta = (datetime.now() - start_time)
			eta = delta / progress * (total_files - progress)
			try:
				eta_str = str(eta)[:str(eta).index(".")]
			except:
				eta_str = str(eta)
			try:
				delta_str = str(delta)[:str(delta).index(".")]
			except:
				delta_str = str(delta)
			print(f"{progress:{len(str(total_files))}d}/{total_files} ({progress*100//total_files:3d}%) [{"="*(progress*100//total_files)}>{" "*(99 - progress*100//total_files)}] ({delta_str} ETA {eta_str} / {(datetime.now()+eta).strftime("%H:%M:%S")})")
			print()
# 通話錄音資料夾不存在則略過
else:
	print(f"[WARNING] plaud_note/CALLS directory not exist.")
	logging.warning(f"plaud_note/CALLS directory not exist.")

# 搬移筆記錄音檔案
notes_dir = path.join(plaud_path, "NOTES")
if path.exists(notes_dir):
	# 走訪所有資料夾
	for record_dir in listdir(notes_dir):
		date_obj = datetime.strptime(record_dir, "%Y%m%d")
		raw_dest_dir = path.join(backup_path, "raw", "NOTES", record_dir)
		transfered_dest_dir = path.join(backup_path, "transfered", f"{record_dir}_{date_obj.strftime("%a")}_notes")

		# 建立目的地資料夾
		try:
			os.makedirs(raw_dest_dir)
		except FileExistsError:
			pass
		except Exception as e:
			print(f"Making directory fail: {e}")
			logging.error(f"Making directory fail: {e}")
		try:
			os.makedirs(transfered_dest_dir)
		except FileExistsError:
			pass
		except Exception as e:
			print(f"Making directory fail: {e}")
			logging.error(f"Making directory fail: {e}")

		# 走訪資料夾內檔案
		for reocrd_files in listdir(path.join(notes_dir, record_dir)):
			raw_file = path.join(notes_dir, record_dir, reocrd_files)
			datetime_obj = datetime.fromtimestamp(int(reocrd_files[:10]))
			record_file_mane = datetime_obj.strftime("%Y%m%d_%a_%H%M%S") + reocrd_files[10:]

			# 複製檔案
			try:
				backup_raw_file = path.join(raw_dest_dir, reocrd_files)
				shutil.copy2(raw_file, backup_raw_file)
				logging.info(f"backup success from {raw_file} to {backup_raw_file}")
			except Exception as e:
				print(f"Error copying file: {e}")
				logging.error(f"Error copying file: {e}")
			try:
				backup_transfered_file = path.join(transfered_dest_dir, record_file_mane)
				shutil.copy2(raw_file, backup_transfered_file)
				logging.info(f"backup success from {raw_file} to {backup_transfered_file}")
			except Exception as e:
				print(f"Error copying file: {e}")
				logging.error(f"Error copying file: {e}")

			# 將錄音檔案依照課程分類存放
			if reocrd_files[10:] == ".WAV":
				has_category = True
				# 計算錄音時間，映射到課程名稱
				audio_length = get_audio_length(raw_file)
				audio_time = int(reocrd_files[:10]) + (audio_length/2)
				datetime_obj_shifted = datetime.fromtimestamp(audio_time)
				weekday, hour = datetime_obj_shifted.strftime("%a"), datetime_obj_shifted.strftime("%p%I")
				try:
					weekNo = (date_obj - datetime.strptime(classID['semister_start'], "%Y/%m/%d")).days // 7
					destination_dir = path.join(my_paths['root_path'], my_paths['destination_path'], classID[classTime[weekday][hour]], "Record", f"week{weekNo:02d}_{date_obj.strftime("%Y%m%d")}")
					try:
						os.makedirs(destination_dir)
					except FileExistsError:
						pass
					except Exception as e:
						print(f"Making directory fail: {e}")
						logging.error(f"Making directory fail: {e}")
					fileIndex = 1
					while path.exists(path.join(destination_dir, f"week{weekNo:02d}_{date_obj.strftime("%Y%m%d")}_{classID['semister']}_{classID[classTime[weekday][hour]+"_zh"]}_{fileIndex}.WAV")):
						fileIndex += 1
					try:
						category_file = path.join(destination_dir, f"week{weekNo:02d}_{date_obj.strftime("%Y%m%d")}_{classID['semister']}_{classID[classTime[weekday][hour]+"_zh"]}_{fileIndex}.WAV")
						shutil.copy2(raw_file, category_file)
						logging.info(f"category success from {raw_file} to {category_file}")
					except Exception as e:
						print(f"Error copying file: {e}")
						logging.error(f"Error copying file: {e}")
				except KeyError:
					logging.warning(f"{datetime_obj.strftime("%a %Y/%m/%d %H:%M:%S")} - {reocrd_files} dismatched.")
					destination_dir = path.join(backup_path, "dismatched", f"{record_dir}_{datetime_obj.strftime("%a")}")
					try:
						os.makedirs(destination_dir)
					except FileExistsError:
						pass
					except Exception as e:
						print(f"Making directory fail: {e}")
						logging.error(f"Making directory fail: {e}")

					try:
						category_file = path.join(destination_dir, f"{datetime_obj.strftime("%a_%Y%m%d_%H%M%S")}.WAV")
						shutil.copy2(raw_file, path.join(destination_dir, f"{datetime_obj.strftime("%a_%Y%m%d_%H%M%S")}.WAV"))
						logging.info(f"dismatch success from {raw_file} to {path.join(destination_dir, f"{datetime_obj.strftime("%a_%Y%m%d_%H%M%S")}.WAV")}")
					except Exception as e:
						print(f"Error copying file: {e}")
						logging.error(f"Error copying file: {e}")
			else:
				has_category = False

			# 檢測複製結果是否成功
			original_md5 = get_md5(raw_file)
			check_raw_md5 = (path.exists(backup_raw_file) and  original_md5 == get_md5(backup_raw_file))
			check_transfered_md5 = (path.exists(backup_transfered_file) and original_md5 == get_md5(backup_transfered_file))
			check_category_md5 = (not has_category) or (path.exists(category_file) and original_md5 == get_md5(category_file))
			check_total_md5 = check_raw_md5 and check_transfered_md5 and check_category_md5
			if check_total_md5:
				success_files.append(raw_file)
			else:
				fail_files.append(raw_file)

			print(f"{"O" if check_total_md5 else "X"} {raw_file}")
			print("\t=>", f"{"O" if check_raw_md5 else "X"}", backup_raw_file)
			print("\t=>", f"{"O" if check_transfered_md5 else "X"}", backup_transfered_file)
			if has_category:
				print("\t=>", f"{"O" if check_category_md5 else "X"}", category_file)
			logging.info(f"{progress:{len(str(total_files))}d}/{total_files} ({progress*100//total_files:3d}%) [{"="*(progress*100//total_files)}>{" "*(99 - progress*100//total_files)}]")
			logging.info(f"{raw_file}...")
			logging.info(f"\t\t=> {"O" if check_raw_md5 else "X"} {backup_raw_file}")
			logging.info(f"\t\t=> {"O" if check_transfered_md5 else "X"} {backup_transfered_file}")
			if has_category:
				logging.info(f"\t\t=> {"O" if check_category_md5 else "X"} {category_file}")

			# 計算預估完成時間
			progress += 1
			delta = (datetime.now() - start_time)
			eta = delta / progress * (total_files - progress)
			try:
				eta_str = str(eta)[:str(eta).index(".")]
			except:
				eta_str = str(eta)
			try:
				delta_str = str(delta)[:str(delta).index(".")]
			except:
				delta_str = str(delta)
			print(f"{progress:{len(str(total_files))}d}/{total_files} ({progress*100//total_files:3d}%) [{"="*(progress*100//total_files)}>{" "*(99 - progress*100//total_files)}] ({delta_str} ETA {eta_str} / {(datetime.now()+eta).strftime("%H:%M:%S")})")
			print()
# 筆記錄音資料夾不存在則略過
else:
	print(f"[WARNING] plaud_note/NOTES directory not exist.")
	logging.warning(f"plaud_note/NOTES directory not exist.")

# 判斷所有檔案複製結果
if len(success_files) == total_files:
	print(f"{"O"*20} Process Success, [{len(success_files)}/{total_files}] files done. {"O"*20}")
	logging.info(f"{"O"*20} Process Success, [{len(success_files)}/{total_files}] files done. {"O"*20}")
else:
	print(f"{"X"*20} Process Failed, [{len(success_files)}/{total_files}] files done. {"X"*20}")
	logging.warning(f"{"X"*20} Process Failed, [{len(success_files)}/{total_files}] files done. {"X"*20}")


# ## Delete contents

# In[ ]:


def delete_contents(del_path):
    for root, directories, files in os.walk(del_path):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
        for directory in directories:
            directory_path = os.path.join(root, directory)
            delete_contents(directory_path)
            os.rmdir(directory_path)

# 若複製結果成功，刪除原始檔案
if len(success_files) == total_files:
    delete_contents(calls_dir)
    delete_contents(notes_dir)
    
    print(f"O Delete all files success.")
    logging.info(f"O Delete all files success.")


# ## Convert ipynb to python file

# In[ ]:


# !jupyter nbconvert --to python record_file_categorization.ipynb

