# 공통 모듈
import time
import serial
import serial.tools.list_ports
from datetime import datetime
import threading

# 웹페이지 접속 모듈
import requests 
import re
# 이메일 전송 모듈
import smtplib
from email.mime.text import MIMEText

# 음성인식 모듈
import speech_recognition as sr

now=datetime.now()
current_time={"시간":now.hour,"분":now.minute}
setup_time={"시간":None,"분":None}

def update_current_time():
    global now, current_time
    while True:
        now=datetime.now()
        current_time={"시간":now.hour,"분":now.minute}
        time.sleep(5) # 10초마다 현재 시간 업데이트

serial_receive_data=""

def serial_read_thread():
    global serial_receive_data
    while True:
        read_data=my_serial.readline()
        serial_receive_data=read_data.decode()
               
# 부저 멜로디
freq_alarm=[392,330,330,350,294,294,262,294,330,350,392,392,392,
                392,330,330,330,350,294,294,262,330,392,392,330,330,330]
dTime_alarm2=[0.3,0.3,0.8,0.3,0.3,0.8,0.3,0.3,0.3,0.3,0.3,0.3,0.8,0.3,
              0.3,0.3,0.3,0.3,0.3,0.8,0.3,0.3,0.3,0.3,0.3,0.3,0.8]

def send_buzzer(freq):
    sendData=f"BUZZER={freq}\n"
    my_serial.write(sendData.encode())

def sound_buzzer(): # 알림 울리기   
    for x in range(len(freq_alarm)): 
        send_buzzer(freq_alarm[x])
        time.sleep(dTime_alarm2[x])
        send_buzzer(0)
        time.sleep(0.1)
        
def send_fnd(data):
    sendData=f"FND={data}\n"
    my_serial.write(sendData.encode())
       
def show_fnd(): # fnd 현재시간 표시 
    current_time=str(now.hour)+"."+str(now.minute)
    send_fnd(current_time)

def set_time_button(max_value): # 시간(시,분)의 max값 숫자를 인자로 받아옴         
    # FND에 값을 표시          
    for x in range(max_value+1):
        send_fnd(x)
        x+=1
        time.sleep(0.5) # fnd에 0.5초간격으로 숫자 증가
            
        if ("BUTTON2=CLICK" in serial_receive_data):
            print(serial_receive_data,end='')
            print("설정되었습니다")
            time.sleep(1.5)
            return x-1 # fnd 표시 시간보다 살짝 늦게 설정되어 -1 해줌 / 설정된 시간 반환
        
        
# 날씨 불러오기
def receive_weather(value):
    # 접속할 url 바인딩 (현재 1시간별 RSS임)
    url="https://www.kma.go.kr/w/rss/dfs/hr1-forecast.do?zone=4615056000" 
    response=requests.get(url) # url에 접속하여 값을 받아옴
    
    temp=re.findall(r'<temp>(.+)</temp>',response.text)
    humi=re.findall(r'<reh>(.+)</reh>',response.text)
    weather=re.findall(r'<wfKor>(.+)</wfKor>',response.text)
    
    if value=="temp":
        return temp
    elif value=="humi":
        return humi
    elif value=="weather":
        return weather

# 날씨 불러와 최빈값 출력
def most_frequent(data):
    count_list=[]
 # count를 담을 리스트 변수 설정
    for x in data: 
        count_list.append(data.count(x))
        # append를 사용하여서 크기를 미리 정하지 않고 초기화 가능
    return data[count_list.index(max(count_list))]

def send_email():
    email_temp=str(most_frequent(receive_weather("temp")))
    email_humi=str(most_frequent(receive_weather("humi")))
    email_weather=str(most_frequent(receive_weather("weather")))

    # 메일 전송
    send_email="kate1588@naver.com" # 보내는 사람 메일
    send_pwd="gksql9838**" # 보내는 사람 메일 비밀번호

    recv_email="kate1588@naver.com" # 받는사람 메일

    smtp_name="smtp.naver.com"
    smtp_port=587

    text="오늘은 대체로 온도: "+email_temp+" 습도: "+email_humi+"이며, 날씨는 "+email_weather+"입니다" # 메일 내용

    msg=MIMEText(text)

    msg['Subject']="지금의 날씨입니다."
    msg['From']=send_email
    msg['To']=recv_email
    print(msg.as_string())

    s=smtplib.SMTP(smtp_name,smtp_port)
    s.starttls()
    s.login(send_email,send_pwd)
    s.sendmail(send_email,recv_email,msg.as_string())
    s.quit()

def voice_recognition():
    while True:
        try:
            r = sr.Recognizer() # 음성인식 객체 생성
            
            with sr.Microphone() as source:
                print("듣고 있습니다...")
                audio = r.listen(source)
                
            stt = r.recognize_google(audio, language='ko-KR')
            print("사용자: " + stt)
        
            if "알람" in stt and "꺼" in stt: 
                    print("알람을 종료합니다")
                    send_buzzer(0)
                    time.sleep(60) # 1분
                    
            elif "날씨" in stt and "알려" in stt :
                print("오늘의 날씨를 메일로 전송했습니다.")
                send_email()
            
        except sr.UnknownValueError:
            print("잘 알아듣지 못했어요.")
        except sr.RequestError as e:
            print(f"오류가 발생하였습니다. 오류원인: {e}") 
            
def main():    
    try:
        global serial_receive_data,setup_time,r
        
        update_thread=threading.Thread(target=update_current_time)
        update_thread.daemon=True
        update_thread.start()
        
        voice_thread=threading.Thread(target=voice_recognition)
        voice_thread.daemon=True
        voice_thread.start()
        
        
        while True :   
            if "BUTTON1=CLICK" in serial_receive_data: # 설정
                print(serial_receive_data,end='')
                print("시간(시)를 설정하겠습니다. 0~24 중 원하는 시간에 버튼 2를 눌러주세요")
                time.sleep(1.5)
                send_fnd(23) # 23를 표시함으로써 시간(시) 설정할 것을 fnd로도 알림
                time.sleep(1.5)
                set_hour=set_time_button(23) # 설정된 시간(시) 반환하여 set_hour global 변수에 저장
                serial_receive_data=""
                
                time.sleep(3) # 시간(시)를 설정한 후 시간(분)을 3초 후에 설정하도록 함
                print("시간(분)를 설정하겠습니다. 0~60 중 원하는 시간에 버튼 2를 눌러주세요") 
                time.sleep(1.5) 
                send_fnd(59) # 59을 표시함으로써 시간(분) 설정할 것을 fnd로도 알림
                time.sleep(1.5)
                set_minute=set_time_button(59) # 설정된 시간(분) 반환하여 set_minute global 변수에 저장
                serial_receive_data=""
                
                setup_time={"시간":set_hour,"분":set_minute}
                print("설정된 시간",setup_time) # 변수에 잘 들어갔는지 확인
                # print("현재시간",current_time) 
                
            if(current_time==setup_time):
                show_fnd() # 설정된 알람시간 fnd에 표시
                print("This is set time")
                sound_buzzer()
                
                r = sr.Recognizer() # 음성인식 객체 생성
            
                with sr.Microphone() as source:
                    print("듣고 있습니다...")
                    audio = r.listen(source)
                
                stt = r.recognize_google(audio, language='ko-KR')
                print("사용자: " + stt)
                
                if "알람" in stt and "꺼" in stt: 
                    print("알람을 종료합니다") # 한번은 울림
                    send_buzzer(0)
                    time.sleep(60) # 1분
                
            #else: 
                #print("This is not set time")
                
            time.sleep(1) # 쓰레드 간 간격을 위해 1초 대기
        
    except KeyboardInterrupt:
        pass



if __name__=='__main__':
    ports=list(serial.tools.list_ports.comports())
    for p in ports:
        if 'Arduino Uno' in p.description:
            print(f"{p} 포트에 연결하였습니다.") # 포트 연결 
            my_serial=serial.Serial(p.device,baudrate=9600,timeout=1.0)
            time.sleep(2.0)
            
    t1=threading.Thread(target=serial_read_thread)
    t1.daemon=True
    t1.start()
            
    main()
                
    my_serial.close()

