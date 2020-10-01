import PySimpleGUI as sg
import threading

bat = '                   '
values = ' '

layout = [[sg.Text('The battery is equal to: ' + bat, key='battery'), sg.Text('   You can now send a command!', key='status')],
          [sg.Input(key='last command'), sg.Button('Execute',bind_return_key=True)] ]
window = sg.Window('Drone Terminal', layout, finalize=True)

def battery():
    read = 0
    while True:
        try:
            read = int(input())
        except ValueError: 
            pass
        if read > 0 and read < 101: 
            bat = str(read)
            window.Element('battery').update("The battery is equal to: " + bat)
        else:
            pass
batteryThread = threading.Thread(target=battery)
batteryThread.start()

def readData():
    window.Element('last command').update("")
    datainput = str(values)
    #Send "data" to the drone
    if datainput == "{'last command': 'takeoff'}" or datainput == "{'last command': 'land'}":
        window.Element('status').update('   Do not send a command!')
        while data != "ok":
            window.Element('status').update('   Do not send a command!')
            if data == "ok":
                window.Element('status').update('   You can now send a command!')
                
while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if event == 'Execute':
        inputThread = threading.Thread(target=readData)
        inputThread.start()     
window.close()
