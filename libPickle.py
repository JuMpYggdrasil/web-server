import pickle
	
def save_pickle_obj(obj, name ):
	with open('/home/pi/flask/web-server/obj/'+ name + '.pkl', 'wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_pickle_obj(name ):
	with open('/home/pi/flask/web-server/obj/' + name + '.pkl', 'rb') as f:
		return pickle.load(f)
		
if __name__ == "__main__":
	DB_dir = "/home/pi/Sensors_Database/sensorData.db"
	save_pickle_obj(DB_dir,'DB_dir')
	#save_pickle_obj(devices,'devices')
	devices = load_pickle_obj('devices')
	print(devices)