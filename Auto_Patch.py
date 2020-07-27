import sys
import paramiko
import os
import time
import csv
import re
import logging
from pyfiglet import Figlet
from colorama import init, Fore

init(autoreset=True)

BLUE = 0x01
GREEN = 0x02
RED = 0x04

Version = "0.5 Beta"
name = "ytkang"

# 라인 구분자 셋
str_next_conn           = "---------------------------- 다음 서버 접속 중 -----------------------------"
str_line1               = "=============================== "
str_line2               = " ==============================="
str_ver_match           = "=============================== 버전 비교 중 ==============================="
str_proc_stop           = "========================= 프로세스를 종료하였습니다.======================="
str_proc_stop_fail      = "========================= 프로세스를 종료하였습니다.======================="
str_sys_chk             = "========================= 시스템을 확인해 주세요.=========================="
str_proc_force_kill     = "======================== 프로세스를 강제 종료 합니다. ======================"
str_proc_run            = "=================== 프로세스가 정상적으로 실행되었습니다.==================="
str_patch_start         = "============================ 서버를 패치 합니다.============================"

# 변수 셋
pgrep_ms            = "ps aux | grep 'master_server' | grep -v 'grep' | wc -l"
pgrep_rs            = "ps aux | grep 'recording_server' | grep -v 'grep' | wc -l"
ms_kill             = "kill -9 `ps -ef | grep '/home/devel/vms/master_server' | grep -v 'grep' | awk '{print $2}'`"
rs_kill             = "kill -9 `ps -ef | grep '/home/devel/vms/recording_server' | grep -v 'grep' | awk '{print $2}'`"
master_stop         = './vms/run_master.sh stop'
rec_stop            = './vms/run_recording.sh stop'
ms_ver_chk          = './vms/master_server -version'
rs_ver_chk          = './vms/recording_server -version'
patch_path          = 'C:\\temp\\patch_file\\'
master_start        = './vms/run_master.sh start'
rec_start           = './vms/run_recording.sh start'
ms_list_csv         = 'C:\\Users\\ytkang\\Documents\\Python연습\\linux_ms.csv'
rs_list_csv         = 'C:\\Users\\ytkang\\Documents\\Python연습\\linux_rs.csv'


ssh = paramiko.SSHClient()                  # SSHClient 변수 생성
ver = re.compile(r'\d.\d.\d.\d{6}')           # 버전 정규식 규칙 생성

mylogger = logging.getLogger("vpatch")
mylogger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('\\log\\vpatch.log')
file_handler.setFormatter(formatter)
mylogger.addHandler(file_handler)


def log_start():
    mylogger.info("=============== Start ===============")


def log_end():
    mylogger.info("================ END ================")


def pscp(item):
    os.system('pscp -r -pw ' + item[2] + ' ' + patch_path + ' devel@' + item[0] + ':/home/devel/vms')


def key_error():
    print("잘못된 키를 입력하였습니다.")
    mylogger.error("잘못된 키를 입력")
    log_end()
    sys.exit(1)


def help_me():
    print("Usage:")
    print("  vpatch [option] <command>")
    print("")
    print("Options:")
    print("  -h, --help               Show Help")
    print("  -l, --liunx              리눅스 서버를 대상")
    print("  -w, --window             윈도우 서버를 대상")
    print("")
    print("Commands:")
    print("  ms                       Master Server")
    print("  rs                       Recording Server")
    print("")
    print("사용예:")
    print("  vpatch -l ms 또는, vpatch --linux ms")
    print("  vpatch -w rs 또는, vpatch --window rs")
    return


def main():
    try:
        if sys.argv[1] == '--window' or sys.argv[1] == '-w':
            if sys.argv[2] == 'ms':
                print("Windows - Master : 준비 중입니다.")
            elif sys.argv[2] == 'rs':
                print("Windows - Recording : 준비 중입니다.")
            else:
                print("두번째 인자값이 틀렸습니다")
        elif sys.argv[1] == '--linux' or sys.argv[1] == '-l':
            if sys.argv[2] == 'ms':
                os_type = sys.argv[1] + sys.argv[2]
                linux(os_type)
            elif sys.argv[2] == 'rs':
                os_type = sys.argv[1] + sys.argv[2]
                linux(os_type)
            else:
                print("두번째 인자값이 틀렸습니다")
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            help_me()
        else:
            print("첫번째 인자값이 틀렸습니다")
    except IndexError:
        help_me()


def login(ip, username, password, item, lastest_ver, os_type):
    try:
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(ip, username=username, password=password, timeout=10)  # 입력받은 서버IP, id, pw를 받아서 접속
        print(Fore.YELLOW + item[0] + " 서버에 로그인 성공하였습니다!")
        mylogger.info(item[0] + " --> 로그인 성공")

        ver_chk(item, lastest_ver, os_type)
    except paramiko.AuthenticationException:
        print(Fore.RED + "로그인 인증에 실패하였습니다.")
        mylogger.error(item[0] + " --> 로그인 인증 실패")
        exit()
    except paramiko.SSHException:
        print(Fore.RED + "SSH Exception!")
        mylogger.info(item[0] + " --> SSH Exception")
    except paramiko.ssh_exception.socket.timeout:
        print(Fore.RED + "Timed out!!")
        mylogger.info(item[0] + " --> Login Timed out")
    finally:
        ssh.close()


def str_1st(item):
    print(Fore.LIGHTGREEN_EX + str_line1 + item[0] + str_line2)
    time.sleep(1)
    print(Fore.CYAN + str_ver_match)
    time.sleep(2)


def ver_chk_real(item, lastest_ver, os_type, a, b):
    str_1st(item)
    stdin, stdout, stderr = ssh.exec_command(a)  # 현재 server 버전 체크
    Current_ver = stdout.read().decode('ascii').replace('Master server version is ', '').replace('Recording server '
                                                                                                 'version is ',
                                                                                                 '').strip("\n")
    print("현재 버전 : ", Current_ver)
    print("최신 버전 : ", lastest_ver)
    stdin, stdout, stderr = ssh.exec_command(b)  # pgrep 명령어로 server 실행 여부 체크하여 값을 3개의 tuple 로 받음
    result = stdout.read().decode('ascii').strip("\n")  # 아스키 코드 변환 및 특정 문자열 잘라내기
    patch_chk(item, lastest_ver, Current_ver, result, os_type)


def ver_chk(item, lastest_ver, os_type):
    if os_type == '--linuxms' or os_type == '-lms':
        ver_chk_real(item, lastest_ver, os_type, ms_ver_chk, pgrep_ms)

    elif os_type == '--linuxrs' or os_type == '-lrs':
        ver_chk_real(item, lastest_ver, os_type, rs_ver_chk, pgrep_rs)


def str_proc_kill(item):
    print(Fore.CYAN + str_proc_stop)
    mylogger.info(item[0] + " --> 프로세스 강제 종료")


def str_proc_kill_fail(item):
    print(Fore.RED + str_proc_stop_fail)
    mylogger.error(item[0] + " --> 프로세스 강제 종료 실패")
    print(Fore.CYAN + str_sys_chk)
    exit()


def proc_kill(service, item):
    if 'successfully' in service:  # service 변수 안에 successfully 라는 문자열이 포함되어 있으면
        print(service)
        print(Fore.CYAN + str_proc_stop)
        mylogger.info(item[0] + " --> 프로세스 종료")
    else:
        print(service)
        print(Fore.RED + str_proc_stop_fail)
        mylogger.info(item[0] + " --> 프로세스 종료 실패")
        time.sleep(2)
        print(Fore.CYAN + str_proc_force_kill)
        mylogger.info(item[0] + " --> 프로세스 강제 종료 시작")
        if 'master_server' in service:
            ssh.exec_command(ms_kill)
            time.sleep(2)
            stdin, stdout, stderr = ssh.exec_command(pgrep_ms)
            result_ms = stdout.read().decode('ascii').strip("\n")
            if result_ms == 0:
                str_proc_kill(item)
            else:
                str_proc_kill_fail(item)
        elif 'recording_server' in service:
            ssh.exec_command(rs_kill)
            time.sleep(2)
            stdin, stdout, stderr = ssh.exec_command(pgrep_rs)
            result_rs = stdout.read().decode('ascii').strip("\n")
            if result_rs == 0:
                str_proc_kill(item)
            else:
                str_proc_kill_fail(item)


def proc_start(os_type):
    if os_type == '--linuxms' or os_type == '-lms':
        stdin, stdout, stderr = ssh.exec_command(master_start)  # master server 시작
        time.sleep(3)
        service = stdout.read().decode('ascii').strip("\n")
        print(service)
    elif os_type == '--linuxrs' or os_type == '-lrs':
        stdin, stdout, stderr = ssh.exec_command(rec_start)  # recording server 시작
        time.sleep(3)
        service = stdout.read().decode('ascii').strip("\n")
        print(service)


def ok_patch(os_type, item):
    print(Fore.GREEN + "최신버전이 정상적으로 패치되었습니다.")
    mylogger.info(item[0] + " --> 최신버전으로 패치 완료")
    time.sleep(1)
    # 프로세스 시작
    proc_start(os_type)
    print(Fore.CYAN + str_proc_run)
    mylogger.info(item[0] + " --> 프로세스 재실행 완료")


def ostype_ver_chk(item, Current_ver, lastest_ver, os_type):
    if os_type == '--linuxms' or os_type == '-lms':
        # 버전 확인 구문 추가
        stdin, stdout, stderr = ssh.exec_command(ms_ver_chk)  # 현재 master server 버전 체크
        Current_ver = stdout.read().decode('ascii').replace('Master server version is ', '').strip("\n")
    elif os_type == '--linuxrs' or os_type == '-lrs':
        # 버전 확인 구문 추가
        stdin, stdout, stderr = ssh.exec_command(rs_ver_chk)  # 현재 recording server 버전 체크
        Current_ver = stdout.read().decode('ascii').replace('Recording server version is ', '').strip("\n")
    patch_match(item, Current_ver, lastest_ver, os_type)


def patch_run(item, lastest_ver, os_type, srv, srv_ver):
    stdin, stdout, stderr = ssh.exec_command(srv)  # server 종료
    time.sleep(3)
    service = stdout.read().decode('ascii').strip("\n")
    proc_kill(service, item)
    time.sleep(2)
    if os.path.isdir(patch_path):  # patch_file 폴더 여부 체크
        # scp 를 이용해서 패치파일 overwrite
        mylogger.info(item[0] + " --> 패치 시작")
        pscp(item)
        print(Fore.LIGHTBLUE_EX + "서버 패치가 완료되었습니다.")
        mylogger.info(item[0] + " --> 패치 완료")
        # 버전 확인 구문 추가
        stdin, stdout, stderr = ssh.exec_command(srv_ver)  # 현재 server 버전 체크
        Current_ver = stdout.read().decode('ascii').replace('Master server version is ', '').replace('Recording '
                                                                                                     'server version '
                                                                                                     'is ',
                                                                                                     '').strip("\n")
        patch_match(item, Current_ver, lastest_ver, os_type)
    else:
        print(Fore.RED + "C:\\Temp 경로에 patch_file 폴더가 존재하지 않습니다.")
        exit()


def patch_match(item, Current_ver, lastest_ver, os_type):
    print("현재 버전 : ", Current_ver)
    print("최신 버전 : ", lastest_ver)

    if lastest_ver == Current_ver:
        ok_patch(os_type, item)
    else:
        print(Fore.RED + "최신버전으로 제대로 패치되지 않았습니다.")
        mylogger.error(item[0] + " --> 패치 실패")


def patch_chk(item, lastest_ver, Current_ver, result, os_type):
    if Current_ver == '':
        print(Fore.RED + "현재 설치된 버전을 확인할 수 없습니다.")
        mylogger.error(item[0] + " --> 현재 설치된 버전을 확인할 수 없음")
        exit()
    elif lastest_ver == Current_ver:
        print(Fore.LIGHTBLUE_EX + "버전이 동일합니다. 패치하지 않겠습니다.")
        mylogger.info(item[0] + " --> 버전 동일. 패치하지 않음")
        time.sleep(2)
    else:
        print(Fore.LIGHTBLUE_EX + "버전이 동일하지 않습니다.")
        time.sleep(2)
        mylogger.info(item[0] + " --> 버전 동일하지 않음")
        if result > '0':  # 결과값이 1일 경우
            print(Fore.LIGHTBLUE_EX + "프로세스가 실행중입니다.")
            mylogger.info(item[0] + " --> 프로세스 실행중 확인")
            time.sleep(1)
            if os_type == '--linuxms' or os_type == '-lms':
                patch_run(item, lastest_ver, os_type, master_stop, ms_ver_chk)
            elif os_type == '--linuxrs' or os_type == '-lrs':
                patch_run(item, lastest_ver, os_type, rec_stop, rs_ver_chk)

        else:  # 결과값이 1이 아닐 경우 (0인 경우)
            print(Fore.LIGHTBLUE_EX + "프로세스가 실행중이 아닙니다.")
            mylogger.info(item[0] + " --> 프로세스 실행 안됨")
            time.sleep(2)
            print(Fore.CYAN + str_patch_start)
            time.sleep(2)
            # scp를 이용해서 패치파일 overwrite
            try:
                if os.path.isdir(patch_path):
                    pscp(item)
                    print(Fore.LIGHTBLUE_EX + "서버 패치가 완료되었습니다.")
                    mylogger.info(item[0] + " --> 패치 완료")
                else:
                    print(Fore.RED + "C:\\Temp 경로에 patch_file 폴더가 존재하지 않습니다.")
                    exit()
            except os.error:
                print(Fore.RED + "정상적으로 실행하지 못했습니다.")
                mylogger.error(item[0] + " --> 패치를 실행하지 못했습니다.")

            ostype_ver_chk(item, Current_ver, lastest_ver, os_type)


def v_screen():
    f = Figlet(font='slant')
    print(f.renderText("VURIX PMS"))
    print("                                 Version : " + Version)
#   print("                               Developer :   " + name)
    print("                                          ")
    try:
        print("")
        print("")
        input("엔터키를 누르세요.")
    except KeyboardInterrupt:
        key_error()
    except EOFError:
        key_error()


def same_list(idx, srv_lst):
    if idx == len(srv_lst) - 1:
        print(Fore.LIGHTBLUE_EX + "더이상 접속할 서버가 없습니다. 자동패치를 종료합니다.")
        mylogger.info("더이상 접속할 서버가 없음")
        log_end()
        # mylogger.info("=============== END ================")
        sys.exit()
    else:
        print(Fore.RED + str_next_conn)


def lst_chk(data, os_type, lm_Srv_lst, lr_Srv_lst, lst_cnt):
    try:
        wh = 0
        while wh < 3:
            wh = wh + 1
            lastest_ver = input("현재 최신 버전을 입력하세요 :")
            ver_match = ver.match(lastest_ver)
            mylogger.info("입력한 최신버전 : " + lastest_ver)
            if ver_match:
                # print('Match found: ', m.group())
                for idx, item in enumerate(data):
                    ip = item[0]
                    username = item[1]
                    password = item[2]
                    lst_cnt = lst_cnt - 1
                    print(Fore.MAGENTA + "현재 남은 서버 :", lst_cnt, "대")
                    login(ip, username, password, item, lastest_ver, os_type)
                    if os_type == '--linuxms' or os_type == '-lms':
                        same_list(idx, lm_Srv_lst)
                    elif os_type == '--linuxrs' or os_type == '-lrs':
                        same_list(idx, lr_Srv_lst)
            else:
                print(Fore.RED + "올바른 버전이 아닙니다. 다시 정확한 버전을 입력해주세요.")
                mylogger.error("입력한 버전이 올바르지 않음")
            if wh == 3:
                print(Fore.RED + "3번 모두 실패하였습니다. 다시 실행하십시오.")
                mylogger.error("로그인 3번 모두 실패")
                log_end()
                sys.exit()
    except KeyboardInterrupt:
        key_error()
    except EOFError:
        key_error()
    except KeyError:
        key_error()


def not_srv_info():
    print(Fore.RED + "서버 정보가 없습니다. 서버리스트 파일을 확인해주세요.")
    mylogger.error("서버 정보 없음. 서버리스트 파일 확인요망")
    log_end()
    sys.exit()


def linux(os_type):
    data = 0
    lst_cnt = 1
    lm_Srv_lst = [str]
    lr_Srv_lst = [str]
    try:
        if os_type == '--linuxms' or os_type == '-lms':
            lm_Srv_lst = open(ms_list_csv, 'r', encoding='utf-8').readlines()
            data = csv.reader(lm_Srv_lst)
            lst_cnt = len(lm_Srv_lst)
            if lm_Srv_lst == ['\n']:
                not_srv_info()
        elif os_type == '--linuxrs' or os_type == '-lrs':
            lr_Srv_lst = open(rs_list_csv, 'r', encoding='utf-8').readlines()
            data = csv.reader(lr_Srv_lst)
            lst_cnt = len(lr_Srv_lst)
            if lr_Srv_lst == ['\n']:
                not_srv_info()
        v_screen()
        lst_chk(data, os_type, lm_Srv_lst, lr_Srv_lst, lst_cnt)
    except IOError:
        print(Fore.RED + "서버 리스트를 불러올 수가 없습니다. 서버리스트 파일을 확인해주세요.")
        mylogger.error("서버 리스트 파일 로드 실패")
        log_end()
        exit()


if __name__ == '__main__':
    log_start()
    main()
