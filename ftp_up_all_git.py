import os
import time
from time import strftime, localtime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ftplib
import ftputil
import ftputil.session

server_config = [
    {
    'name': 'server one',
    'ftp_host' : 'domain.com',
    'ftp_user' : 'ftp user',
    'ftp_pass' : 'ftp password',
    'ftp_port' : 21,
    'watch_path' : '/local/watch/path/', # must be contain "/" first & last position
    'remote_path' : '/server/path/', # must be contain "/" first & last position
    'replace_dir' : 'public',
    'target_dir' : 'public_html',
    'ignore' : [".vscode", ".git", ".DS_Store"]
    },
    {
    'name': 'server two',
    'ftp_host' : 'domain.com',
    'ftp_user' : 'ftp user',
    'ftp_pass' : 'ftp password',
    'ftp_port' : 21,
    'watch_path' : '/local/watch/path/', # must be contain "/" first & last position
    'remote_path' : '/server/path/', # must be contain "/" first & last position
    'replace_dir' : 'public',
    'target_dir' : 'httpdocs',
    'ignore' : [".vscode", ".git", ".DS_Store"]
    }
]

for i in range (0,len(server_config)):
    print(str(i)+' => '+server_config[i]['name'])
select_server = int(input('Type server serial number: '))

ftp_host = server_config[select_server]['ftp_host']
ftp_user = server_config[select_server]['ftp_user']
ftp_pass = server_config[select_server]['ftp_pass']
ftp_port = server_config[select_server]['ftp_port']
watch_path = server_config[select_server]['watch_path']
remote_path = server_config[select_server]['remote_path']
replace_dir = server_config[select_server]['replace_dir']
target_dir = server_config[select_server]['target_dir']
ignore = []
for i in range (0, len(server_config[select_server]['ignore'])):
    ignore.append(server_config[select_server]['ignore'][i])
print(server_config[select_server]['name']+ " is selected and config loaded!")


def connect_ftp():

    ftp = ftplib.FTP_TLS()
    ftp.connect(ftp_host, ftp_port)
    ftp.login(ftp_user, ftp_pass)
    ftp.prot_p()
    return ftp

def ftp_util_del(ftp_con, remote_path, target_file):
    ftp_con.quit()
    ftp_con.close()
    my_session_factory = ftputil.session.session_factory(base_class=ftplib.FTP_TLS)
    ftp_util =ftputil.FTPHost(ftp_host, ftp_user, ftp_pass, session_factory=my_session_factory)
    ftp_util.rmtree(remote_path+target_file)

def upload_file(ftp_connection, upload_file_path, target_file_path):
    try:
        read_file = open(upload_file_path, 'rb')
        print('Uploading ' + upload_file_path + "...")
        ftp_connection.storbinary('STOR ' + target_file_path, read_file)
        read_file.close()
        print(strftime("%Y-%m-%d %H:%M:%S", localtime()),' - Upload finished!!')
    except Exception as e:
        print("Error uploading file: " + str(e))

def dir_create(ftp_con, remote_path, target_folder):
    try:
        if target_folder not in ftp_con.nlst(remote_path):
            ftp_con.mkd(remote_path+target_folder)
    except:
        pass
    
def dir_delete(ftp_con, remote_path, target_folder):
    try:
        if target_folder in ftp_con.nlst(remote_path):
            ftp_con.rmd(remote_path+target_folder)
    except:
        pass
    
def dir_exist_subDir(ftp_con, remote_path, target_folder_list):
    for i in range (0, len(target_folder_list)):
        dir_create(ftp_con, remote_path, target_folder_list[i])
        remote_path += target_folder_list[i]+'/'

old = 0
ftp = connect_ftp()
print('Connected!!')
class chk_event_handler(FileSystemEventHandler):
    
    def on_any_event(self, event):
        global ftp
        global old
        src_filePath = event.src_path
        
        if event.is_directory == True:
            src_folder_list = src_filePath.split('/')[len(watch_path.split('/'))-1:]
            for n, i in enumerate(src_folder_list):
                if i == replace_dir:
                    src_folder_list[n] = target_dir
            src_fileFolder = '/'.join(src_folder_list)
        elif event.is_directory == False:
            src_folder_list = src_filePath.split('/')[len(watch_path.split('/'))-1:-1]
            for n, i in enumerate(src_folder_list):
                if i == replace_dir:
                    src_folder_list[n] = target_dir
            src_fileFolder = '/'.join(src_folder_list)
            src_fileName = src_filePath.split('/')[-1]
        
        try:
            ftp.voidcmd("NOOP")
            print('Still Connected!!')
        except:
            ftp = connect_ftp()
            print('Connected again!!')
        
        # for dir created
        if event.event_type == 'created' and event.is_directory == True:
            print('Creating ' + src_filePath + "...")
            dir_exist_subDir(ftp, remote_path, src_folder_list)
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), ' - Folder Created!')
            
        # for dir renamed
        elif event.event_type == 'moved' and event.is_directory == True:
            src_rename_dir = src_filePath.split(watch_path)[1]
            dest_rename_dir =(event.dest_path).split(watch_path)[1]
            print('Renameing ' + src_filePath + "...")
            ftp.rename(src_rename_dir, dest_rename_dir)
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), ' - Folder Renamed!')
            
        # for dir deleted
        elif event.event_type == 'deleted' and event.is_directory == True:
            print('Deleting ' + src_filePath + "...")
            ftp_util_del(ftp, remote_path, src_fileFolder)
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), ' - Folder Deleted!')
            
        # for file created
        elif event.event_type == 'created' and event.is_directory == False and src_fileName not in ignore:
            dir_exist_subDir(ftp, remote_path, src_folder_list)
            upload_file(ftp, src_filePath, src_filePath.split(watch_path)[1])
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()),' - File Created!')
            
        # for file renamed
        elif event.event_type == 'moved' and event.is_directory == False  and src_fileName not in ignore:
            src_rename_file = src_filePath.split(watch_path)[1]
            dest_rename_file =(event.dest_path).split(watch_path)[1]
            print('Renameing ' + src_filePath + "...")
            ftp.rename(src_rename_file, dest_rename_file)
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), ' - File Renamed!')
            
        # for file delete
        elif event.event_type == 'deleted' and event.is_directory == False  and src_fileName not in ignore:
            print('Deleting ' + src_filePath + "...")
            ftp.delete(src_filePath.split(watch_path)[1])
            print(strftime("%Y-%m-%d %H:%M:%S", localtime()), ' - File Deleted!')
            
        # for file modified
        elif event.event_type == 'modified' and event.is_directory == False  and src_fileName not in ignore:
            try:
                statbuf = os.stat(event.src_path)
                new = statbuf.st_mtime
                if (new - old) > 0.5:
                    dir_exist_subDir(ftp, remote_path, src_folder_list)
                    upload_file(ftp, src_filePath, src_filePath.split(watch_path)[1])
                    print(strftime("%Y-%m-%d %H:%M:%S", localtime()),' - File Modified!')
                old = new
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    
    event_handler = chk_event_handler()
    observer = Observer()
    observer.schedule(event_handler, watch_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
