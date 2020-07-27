# Python_AutoPatch
 서버리스트(.CSV)로부터 서버 정보를 전달받아 순차적으로 서버에 접속하여 버전 비교 및 프로세스 종료-실행을 통해 패치 자동화 구현

[Usage:]

AutoPatch [option] <command>
Options:
      -h, --help               Show Help
      -l, --liunx              리눅스 서버를 대상
      -w, --window             윈도우 서버를 대상

Commands:
      ms                       Master Server
      rs                       Recording Server

사용예:
      AutoPatch -l ms 또는, AutoPatch --linux ms
      AutoPatch -w rs 또는, AutoPatch --window rs
      
※ 현재 Windows는 작업 진행 중..
