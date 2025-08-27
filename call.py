from pyVoIP.VoIP import VoIPPhone, InvalidStateError, CallState
import time
import wave

def answer(call):
    print("got call")
    try:
        f = wave.open('announcment.wav', 'rb')
        frames = f.getnframes()
        data = f.readframes(frames)
        f.close()
        
        print(f)

        call.answer()
        call.write_audio(data)  # This writes the audio data to the transmit buffer, this must be bytes.
        stop = time.time() + (frames / 8000)  # frames/8000 is the length of the audio in seconds. 8000 is the hertz of PCMU.

        while time.time() <= stop and call.state == CallState.ANSWERED:
            time.sleep(0.1)
        
        
        call.hangup()
    except InvalidStateError:
        pass
    except:
        call.hangup()

def calling(call):
    try:
        print("wait for pickup")
        while (call.state is not CallState.ANSWERED):
          print(call.state)
          time.sleep(0.5)
        time.sleep(2)
        f = wave.open('../Desktop/Garage2/output.wav', 'rb')
        data = f.readframes(160)
        print(data)
        while data:
            call.write_audio(data)
            data = f.readframes(160)

        f.close()
        time.sleep(1)
        print("wait for input from phone")
        while call.state == CallState.ANSWERED:
            dtmf = call.get_dtmf()
            print(F"DTMF: {dtmf}")
            if dtmf == "1":
                # Do something
                print("yeah")
                call.hangup()
            elif dtmf == "2":
                # Do something else
                call.hangup()
            time.sleep(0.1)
        print("end of call")
    except InvalidStateError as e:
        print(e)
        pass
    except Exception as e:
        print(e)
        call.hangup()

if __name__ == "__main__":
    phone = VoIPPhone("192.168.188.1", 5060, "raspiphone" , "...", myIP="...", callCallback=answer)
    phone.start()
#    input('Press enter to disable the phone')
    #time.sleep(5)
    call=phone.call("**1")
    calling(call)
    input("press any key")
    phone.stop()
