from telegram.ext import *
from telegram import InputFile
import io
import database
import sys
import os
from pymongo import MongoClient
import re
import random
import smtplib

key='mongodb+srv://Venkataswarao:Kvr*112218@cluster0.lqxzvm9.mongodb.net/?retryWrites=true&w=majority&ssl=true'
bot_key='5871303486:AAEaYo-g1lpw-Vw0OZTWkPz9PVK5OHHjbCU'


conversation_timeout=300

# monkey-patch the requests library

updater=Updater(bot_key,use_context=True)
bot=updater.bot

REGISTER,USERNAME,VERIFY,EMAIL,PASSWORD=range(11,16)
START,EMAIL,PASSWORD,FILES,GET=range(5)
DELETE,DEMAIL,DPASSWORD,DFILES,DGET=range(5,10)
FEMAIL,FVERIFY,FPASSWORD=range(21,24)
UPLOAD,UEMAIL,UPASSWORD,RUPLOAD,UFILE=range(31,36)
def cancel(update,context):
    #update.message.reply_text('conversation ended ...')
    return ConversationHandler.END
def clear(update,context):
    update.message.reply_text('clearing ...')
    chat_id=update.message.chat_id
    try:
        context.bot.delete_message(chat_id,update.message.message_id+1)
        for i in range(1000):
            context.bot.delete_message(chat_id,update.message.message_id-i)   
        
    except Exception as e:
        pass
    finally:
        return cancel
    try:
        context.bot.delete_message(chat_id,update.message.message_id+2)
        context.bot.delete_message(chat_id,update.message.message_id+3)
        context.bot.delete_message(chat_id,update.message.message_id+4)
        context.bot.delete_message(chat_id,update.message.message_id+5)
    except Exception as e:
        pass
    finally:
        return cancel
    
def start(update,context):
    update.message.reply_text('Enter Email Id  ...')
    return EMAIL
def vemail(update,context,p=0):
    
    if p==0:
        email,context.user_data['email']=update.message.text,update.message.text
        data=database.find_user(email)
        while data==None:
            update.message.reply_text('''user not found !
Enter Registered Mail Id ..
New user ? ( /create_locker ) ...
''')
            return EMAIL
        update.message.reply_text('Enter password ...')
    return PASSWORD
def vpassword(update,context):
    password,context.user_data['password']=update.message.text,update.message.text
    data=database.find_user(context.user_data['email'])
    while password!=data['password']:
        update.message.reply_text('wrong password !')
        return vemail(update,context,p=1)
    update.message.reply_text(f'''Hey there {data['username']} !
    
Locker space : {round(data['storage']/1000,3)} MB !

Hang in there Loading your files ...
                              ''')
    

    return files(update,context)
def files(update,context):

    files=database.find_files(context.user_data['email'])


    if len(files['filename'])!=0:
        update.message.reply_text('your locker files are ...')
        for i,(file_name,file_size) in enumerate(zip(files['filename'],files['sizes'])):
            update.message.reply_text(f'{i+1}.  {file_name}')
            context.user_data[str(i+1)]=file_name
            context.user_data[file_name]=str(i+1)
        update.message.reply_text('what files do you need (enter number ..) ?')
    else:
        update.message.reply_text('Locker is Empty !')
        update.message.reply_text('upload files using : /upload')
        return cancel(update,context)
    
    return GET

def get(update,context):
    
    filenumbers,context.user_data['filename']=update.message.text,update.message.text
    filenumbers=re.split(' |,',filenumbers)
    
    try:
        if '.' in filenumbers[0]:
            filenames=','.join(filenumbers)
        else:
            filenames=','.join([context.user_data[filenumber] for filenumber in filenumbers])
        
        email=context.user_data['email']
        
        data=database.get_file(email,filenames)
        if data!=None:
            update.message.reply_text('downloading ...')
        for file in data:
            
            file_data=io.BufferedReader(io.BytesIO(data[file]['data']))
            file_data=InputFile(file_data,file)
                
            bot.send_document(update.message.chat_id,file_data)


    except KeyError:
        update.message.reply_text('file not found ...')

#registration process ...
        
def send_otp(email):
    sender='doclocker3@gmail.com'
    password='xivqwisxuyvhiveu'
    otp=random.randint(10000,99999)
    message='Your OTP  '+str(otp)#is there is ' : ' in it then you can't see the message(otp) in your mail
    server=smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(sender,password)
    server.sendmail(sender,email,message)
    
    print('otp sent : '+str(otp))
    return str(otp)


def register(update,context):
    storage=database.total_storage()
    if storage>=450:
        update.message.reply_text('Sorry no more lockers are available ... !')
        return cancel(update,context)
    
    
    update.message.reply_text("Alright,a new Locker. what's your name ...")
    
    
    return USERNAME
def username(update,context):
    
    username,context.user_data['username']=(update.message.text).lower(),(update.message.text).lower()
    data=database.find_name(username)
    if data!=None:
        update.message.reply_text('Hmmm... Heard before !')
    update.message.reply_text('Enter your Mail Id ...')
    return EMAIL
def email(update,context):
    email,context.user_data['email']=update.message.text,update.message.text
    data=database.find_user(email)
    
    while data!=None:
        update.message.reply_text('You already had a Locker ! ...')
        update.message.reply_text('Enter another Mail Id ...')
        return EMAIL
    try:
        otp=send_otp(email)
        context.user_data['otp']=otp
        update.message.reply_text('Enter OTP sent to the Mail (check Junk Email) ...')
        return VERIFY
    except Exception as e:
        update.message.reply_text('Please Enter a valid Mail ID ...!')
        print(e)
    
def verify(update,context):
    otp=update.message.text
    while otp!=context.user_data['otp']:
        update.message.reply_text('Wrong OTP')
        return VERIFY
    update.message.reply_text('Enter New password ...')
    return PASSWORD
def password(update,context):
    passwd,context.user_data['new_password']=update.message.text,update.message.text
    username=context.user_data['username']
    email=context.user_data['email']
    status=database.create_user(username,email,passwd)
    if status==1:
        update.message.reply_text('''Locker created
Upload files into it : /upload
''')
        
        return cancel(update,context)
    else:
        update.message.reply_text('Something went wrong ...')


        
def help_me(update,context):
    update.message.reply_text('''/start - Start to access your Locker
/create_locker - Create a Locker with Intangible security
/logout - Clear's all the chat History and closes
/forget - reset your locker password
/upload - upload files to your locker
/delete - delete your files

****************************
NOTE:
    The Mail-Id you provide is case sensitive !
    
If you're facing any problem, Please "CLEAR CHAT HISTORY" and retry.

    Still facing the problem?
    Reach us at : doclocker3@gmail.com'''
                              )
    return cancel(update,context)
def forget_password(update,context):
    update.message.reply_text('Alright , Enter your Mail Id : ')
    return FEMAIL
def femail(update,context):
    email,context.user_data['femail']=update.message.text,update.message.text
    user=database.find_user(email)
    while user==None:
        update.message.reply_text('''user not found !
Enter registerd Mail Id ...
                                  ''')
        return FEMAIL
    try:
        otp=send_otp(email)
        context.user_data['fotp']=otp
        update.message.reply_text('Enter OTP sent to the Mail (check Junk Email) ...')
        return FVERIFY
    except Exception as e:
        update.message.reply_text('Please Enter a valid Mail ID ...!')
        print(e)
def fverify(update,context):
    otp=update.message.text
    while otp!=context.user_data['fotp']:
        update.message.reply_text('Wrong OTP')
        return FVERIFY
    update.message.reply_text('Enter new password ...')
    return FPASSWORD
def fpassword(update,context):
    passwd=update.message.text
    email=context.user_data['femail']
    status=database.update_password(email,passwd)
    if status==1:
        update.message.reply_text('Successfully updated ...')
    else:
        update.message.reply_text('Something went wrong ...')
    return cancel(update,context)
def upload(update,context):
    update.message.reply_text('enter Locker Mail Id ...')
    return UEMAIL
def uemail(update,context,p=0):
    email,context.user_data['email']=update.message.text,update.message.text
    data=database.find_user(email)
    while data==None:
        update.message.reply_text('''user not found !
Enter Registered Mail Id ..
''')
        return UEMAIL
    update.message.reply_text('Enter password ...')
    return UPASSWORD
def upassword(update,context):
    password,context.user_data['password']=update.message.text,update.message.text
    data=database.find_user(context.user_data['email'])
    while password!=data['password']:
        update.message.reply_text('wrong password !')
        return UPASSWORD
    if data['storage']<=50:
        update.message.reply_text(f'''sorry {data["username"]}

Your locker is Full ...
''')
        return cancel(update,context)
    update.message.reply_text(f'''Hey there {data['username']} !

Your locker remaining storage : {round(data['storage']/1000,4)} MB !

Send me the file you want to upload ...

NOTE : upload the file with less size for faster bot experience ..!

IF you want to store your video or photo in same quality without compression share it as a document !
''')
    return UFILE

def ready_upload(update,context):
    try:
        filesize=context.user_data['filesize']
        file=context.user_data['file']
        email=context.user_data['email']
        filename,context.user_data['filename']=update.message.text.lower(),update.message.text.lower()
        filename+=f'.{context.user_data["type"]}'
            
        user=database.find_user(email)
        if filesize>=user['storage']:
            update.message.reply_text(f'''out of your remaining Locker Storage !
Choose a file with lower size ...
''')
            return UFILE
        if database.file_already_exists(filename,email)==1:
            update.message.reply_text(f''' File already exits ...!
please choose another file name !

''')
            return RUPLOAD
        update.message.reply_text('Uploading ....')
        status=database.upload_file(filename,filesize,file,email)
        if status==1:
            update.message.reply_text(f'''Successfully uploded ...

Remaining space : {round(database.find_user(email)['storage']/1000,4)} MB !

''')
        else:
            update.message.reply_text('Failed to upload the file ... !')
        return UFILE
    except Exception as e:
        return cancel(update,context)
        print(e)

def uphoto(update,context):
    try:
        
        email=context.user_data['email']
        file=update.message.photo[-1].get_file()
        filesize=round(file.file_size/1000,4)
        update.message.reply_text('Name the file ...')
        d={'filesize':filesize,'file':file,'email':email,'type':'jpg'}
        l=['type','filesize','file','email']
        for i in l:
            context.user_data[i]=d[i]
        return RUPLOAD
    except Exception as e:
        print(e)
        
        
def uaudio(update,context):
    try:
        
        email=context.user_data['email']
        file_id=update.message.audio.file_id
        filename=update.message.audio.file_name
        filesize=round(update.message.audio.file_size/1000,4)
        file=bot.get_file(file_id)
        update.message.reply_text('Name the file ...')
        d={'filesize':filesize,'file':file,'email':email,'type':'mp3'}
        l=['type','filesize','file','email']
        for i in l:
            context.user_data[i]=d[i]
        return RUPLOAD
    except Exception as e:
        print(e)
        
def uvideo(update,context):
    try:
        
        email=context.user_data['email']
        file=update.message.video.get_file()
        filesize=round(file.file_size/1000,4)
        update.message.reply_text('Name the file ...')
        d={'filesize':filesize,'file':file,'email':email,'type':'mp4'}
        l=['type','filesize','file','email']
        for i in l:
            context.user_data[i]=d[i]
        return RUPLOAD
    except Exception as e:
        print(e)
        

def udocument(update,context):
    try:
        
        email=context.user_data['email']
        file_id=update.message.document.file_id
        filename=update.message.document.file_name
        filesize=round(update.message.document.file_size/1000,4)
        file=bot.get_file(file_id)
        file_type=str(update.message.document.mime_type).split('/')[-1]
        if file_type=='webm':
            file_type='mp4'
        elif file_type=='x-python':
            file_type='py'
          
        
        elif file_type=='plain':
            file_type='txt'
        elif file_type=='vnd.openxmlformats-officedocument.wordprocessingml.document':
            file_type='docx'
        update.message.reply_text('Name the file ...')
        d={'filesize':filesize,'file':file,'email':email,'type':file_type}
        l=['type','filesize','file','email']
        for i in l:
            context.user_data[i]=d[i]
        return RUPLOAD
    except Exception as e:
        print(e)

def delete(update,context):
    update.message.reply_text('Enter Email Id  ...')
    return DEMAIL
def demail(update,context,p=0):
    
    if p==0:
        email,context.user_data['email']=update.message.text,update.message.text
        data=database.find_user(email)
        while data==None:
            update.message.reply_text('''user not found !
Enter Registered Mail Id ..
''')
            return DEMAIL
        update.message.reply_text('Enter password ...')
    return DPASSWORD
def dpassword(update,context):
    password,context.user_data['password']=update.message.text,update.message.text
    data=database.find_user(context.user_data['email'])
    while password!=data['password']:
        update.message.reply_text('wrong password !')
        return DPASSWORD
    update.message.reply_text(f'''Hey there {data['username']} !

Hang in there accessing your files ...
                              ''')
    

    
    return dfiles(update,context)
def dfiles(update,context):

    files=database.find_files(context.user_data['email'])
    

    if len(files['filename'])!=0:
        update.message.reply_text('your locker files are ...')
        for i,(file_name,file_size) in enumerate(zip(files['filename'],files['sizes'])):
            update.message.reply_text(f'{i+1}.  {file_name}')
            context.user_data[str(i+1)]=file_name
            context.user_data[file_name]=str(i+1)
            
        update.message.reply_text('what files do you need to remove (enter number ..) ?')
    else:
        update.message.reply_text('Locker is Empty !')
        
        return cancel(update,context)
    
    return DGET

def dget(update,context):
    
    filenumbers,context.user_data['filename']=update.message.text,update.message.text
    filenumbers=re.split(' |,',filenumbers)
    
    try:
        if '.' in filenumbers[0]:
            filenames=','.join(filenumbers)
        else:
            filenames=','.join([context.user_data[filenumber] for filenumber in filenumbers])
        
        email=context.user_data['email']
        update.message.reply_text('deleting ...')
        status=database.delete_file(email,filenames)
        if status==1:
            update.message.reply_text(f'''Successfully deleted ...

Remaining space : {round(database.find_user(email)['storage']/1000,4)} MB !
''')
            update.message.reply_text('Remaining locker files are ....')
            files=database.find_files(context.user_data['email'])
            if len(files['filename'])!=0:
                
                for i,(file_name,file_size) in enumerate(zip(files['filename'],files['sizes'])):
                    update.message.reply_text(f'{i+1}.  {file_name}')
                    context.user_data[str(i+1)]=file_name
                    context.user_data[file_name]=str(i+1)
            else:
                update.message.reply_text('Locker is Empty !')
                update.message.reply_text('upload files using : /upload')
                return cancel(update,context)
            
            
        else:
            update.message.reply_text('file not found !')
    except KeyError:
        update.message.reply_text('file not found ...')  
    

    
def main():
    print('bot started ...')
    start_conv=ConversationHandler(
        entry_points=[CommandHandler('start',start)],
        states={
            START:[MessageHandler(Filters.text &(~ Filters.command),start)],
            EMAIL:[MessageHandler(Filters.text & (~ Filters.command),vemail)],
            PASSWORD:[MessageHandler(Filters.text &(~Filters.command) ,vpassword)],
            FILES:[MessageHandler(Filters.text &(~Filters.command),files)],
            GET:[MessageHandler(Filters.text &(~Filters.command),get)]
            },
        fallbacks=[MessageHandler(Filters.command,cancel)],
        allow_reentry=True,
        conversation_timeout=conversation_timeout
        )
    delete_conv=ConversationHandler(
        entry_points=[CommandHandler('delete',delete)],
        states={
            DELETE:[MessageHandler(Filters.text &(~ Filters.command),delete)],
            DEMAIL:[MessageHandler(Filters.text & (~ Filters.command),demail)],
            DPASSWORD:[MessageHandler(Filters.text &(~Filters.command) ,dpassword)],
            DFILES:[MessageHandler(Filters.text &(~Filters.command),dfiles)],
            DGET:[MessageHandler(Filters.text &(~Filters.command),dget)]
            },
        fallbacks=[MessageHandler(Filters.command,cancel)],
        allow_reentry=True,
        conversation_timeout=conversation_timeout
        )
    register_conv=ConversationHandler(
        entry_points=[CommandHandler('create_locker',register)],
        states={
            REGISTER:[MessageHandler(Filters.text &(~ Filters.command),register)],
            USERNAME:[MessageHandler(Filters.text &(~ Filters.command),username)],
            EMAIL:[MessageHandler(Filters.text & (~ Filters.command),email)],
            VERIFY:[MessageHandler(Filters.text &(~Filters.command),verify)],
            PASSWORD:[MessageHandler(Filters.text & (~Filters.command),password)]
            },
        fallbacks=[MessageHandler(Filters.command,cancel)],
        allow_reentry=True,
        conversation_timeout=conversation_timeout
        )
    upload_conv=ConversationHandler(
        entry_points=[CommandHandler('upload',upload)],
        states={
            UPLOAD:[MessageHandler(Filters.text | Filters.command,upload)],
            UEMAIL:[MessageHandler(Filters.text & ( ~ Filters.command),uemail)],
            UPASSWORD:[MessageHandler(Filters.text | Filters.command,upassword)],
            UFILE:[MessageHandler(Filters.command | Filters.photo ,uphoto),
                   MessageHandler(Filters.command | Filters.audio ,uaudio),
                   MessageHandler(Filters.command | Filters.document ,udocument),
                   MessageHandler(Filters.command | Filters.video ,uvideo),

                   ],
            RUPLOAD:[MessageHandler(Filters.command | Filters.text,ready_upload)],
            },
        fallbacks=[MessageHandler(Filters.command,cancel)],
        allow_reentry=True,
        conversation_timeout=conversation_timeout
        )
    forget_conv=ConversationHandler(
        entry_points=[CommandHandler('forget',forget_password)],
        states={
            FEMAIL:[MessageHandler(Filters.text & (~Filters.command),femail)],
            FPASSWORD:[MessageHandler(Filters.text & (~Filters.command),fpassword)],
            FVERIFY:[MessageHandler(Filters.text & (~Filters.command),fverify)],
            },
        fallbacks=[MessageHandler(Filters.command,cancel)],
        allow_reentry=True,
       conversation_timeout=conversation_timeout
        )
    dp=updater.dispatcher
    
    dp.add_handler(start_conv,1)
    dp.add_handler(register_conv,2)
    dp.add_handler(CommandHandler('logout',clear),3)
    dp.add_handler(CommandHandler('help',help_me),4)
    dp.add_handler(forget_conv,5)
    dp.add_handler(upload_conv,6)
    dp.add_handler(delete_conv,7)
    try:
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print(e)
main()
