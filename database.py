from pymongo import MongoClient
import re
import bson

key='mongodb+srv://Venkataswarao:Kvr*112218@cluster0.lqxzvm9.mongodb.net/?retryWrites=true&w=majority'
client=MongoClient(key)

database=client.doclocker
collection1=database.autentication
collection2=database.locker
print('successfully connected to database...')


def create_user(username,email,password):
    try:
        doc={
            'username':username,
            'email':email,
            'password':password,
            'storage':30000
            }
        collection1.insert_one(doc)
        print('doc inserted ..')
        return 1
    except Exception as e:
        print(e)
        return e
def find_name(username):
    
    user=collection1.find_one({'username':username})
    return user
def update_password(email,password):
    try:
        change={
            '$set':{'password':password}
            }
        collection1.update_many({'email':email},change)
        return 1
    except Exception as e:
        print(e)
        return 0
def total_storage():
    storage=0
    data=collection1.find()
    for i in range(len(list(data))-1):
        storage+=30
        
    creator_storage=80
    return storage+creator_storage
def find_user(email):
    user=collection1.find_one({'email':email})
    return user
def delete_file(email,filenames):
    filenames=re.split(',',filenames)
    try:
        for filename in filenames:
            file=collection2.find_one({'email':email,'filename':filename})
            collection2.delete_one({'email':email,'filename':filename})
            
            change={
                '$set':{'storage':find_user(email)['storage']+file['filesize']}
                }
            collection1.update_one({'email':email},change)
        print('deleted ...')
        return 1
    except Exception as e:
        print(e)
        return 0
def file_already_exists(filename,email):
    data=collection2.find_one({'email':email,'filename':filename})
    if data==None:
        return 0
    else:
        return 1
def find_files(email):
    docs={'filename':[],'sizes':[]}
    
    data=collection2.find({'email':email})
    
    for file in data:
        docs['filename'].append(file['filename'])
        docs['sizes'].append(file['filesize'])
    return docs
def get_file(email,filenames):
    
    filenames=re.split(',',filenames)
    
    docs={}
    for filename in filenames:
        file=collection2.find_one({'email':email,'filename':filename})
        docs[filename]=file
    return docs
def upload_file(filename,filesize,data,email):
    try:
        bson_file=bson.binary.Binary(data.download_as_bytearray())
        user=collection1.find_one({'email':email})
        doc={
            'email':email,
            'filename':filename,
            'filesize':filesize,
            'data':bson_file
            }
        change={
            '$set':{'storage':user['storage']-filesize}
            }
        
        collection2.insert_one(doc)
        collection1.update_one({'email':email},change)
        print('successfully uploaded ...')
        return 1
    except Exception as e:
        print(e)
        return 0
    
    
