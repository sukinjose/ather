#Libraries Importation
from flask import Flask, render_template, redirect, url_for, jsonify, request, send_file
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cv2
import pyzbar.pyzbar as pyzbar
from datetime import datetime
from twilio.rest import Client
import RPi.GPIO as GPIO
import time
import qrcode
from io import BytesIO
from base64 import b64encode
import ast

#Global Initializations
app = Flask(__name__)
cam_done = False  
disp_done = False
qrinfo = ""
p_name = "" 
mqlist = []
phone = ""
ID = ""
disquan = []
displist = []
nalist = []

GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.output(12, True)
GPIO.output(16, True)
GPIO.output(13, True)
GPIO.output(19, True)
# Define the scope and load credentials
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name("/home/pi/Medicart/medicart-414205-8f32bcfbf0a1.json", scope)
gc = gspread.authorize(credentials)



# OTP Setup
account_sid = "AC4f2166f1ed13efc060f4e85e50ae76f3"
auth_token = "32652f1c1915e41b1f782b35fd331d4f"
verify_sid = "VAe031e5e38a5ef586b5416545801e7c7d"

def check_id(num):
    gc = gspread.authorize(credentials)
    sheet = gc.open('Medicart_lookup').worksheet('Pending')
    first_column_values = sheet.col_values(1)
    for row_index, value in enumerate(first_column_values, start=1):  # start=1 to match spreadsheet indexing
        if value == num:
            current_stat = sheet.cell(row_index, 3).value
            return current_stat
    return "Fresh"
            
def id_update(ID, stat):
    gc = gspread.authorize(credentials)
    sheet = gc.open('Medicart_lookup').worksheet('Pending')
    next_empty_row = len(sheet.get_all_values()) + 1
    # Assuming ID goes to the first column and stat to the third column
    sheet.update_cell(next_empty_row, 1, ID)
    sheet.update_cell(next_empty_row, 3, stat)


    

def dispense(slots):
    global disp_done
    for i in slots:
        print("Done")
        if i=='1':
            GPIO.output(12, False)
            time.sleep(1)
            GPIO.output(12, True)
            time.sleep(1)        
        elif i=='2':
            GPIO.output(16, False)
            time.sleep(1)
            GPIO.output(16, True)
            time.sleep(1) 
        elif i=='3':
            GPIO.output(13, False)
            time.sleep(1)
            GPIO.output(13, True)
            time.sleep(1) 
        elif i=='4':
            GPIO.output(19, False)
            time.sleep(1)
            GPIO.output(19, True)
            time.sleep(1)
        else : continue
    disp_done = True
    
def availupdate(a):
    gc = gspread.authorize(credentials)
    sheet = gc.open('Medicart_lookup').worksheet('Availability')
    disp_column_values = sheet.col_values(4)
    for item in a:
        for row_index, value in enumerate(disp_column_values, start=1):  # start=1 to match spreadsheet indexing
            if value == item:
                    current_value = sheet.cell(row_index, 3).value
                    # Attempt to convert the current value to an integer and decrement it by 1
                    new_value = int(current_value) - 1
                    # Ensure the new value does not go below 0
                    new_value = max(0, new_value)
                    # Update the cell with the new value
                    sheet.update_cell(row_index, 3, new_value)

def withdraw_update(a,b):
    ls1, ls2 = medstring_format(b)
    gc = gspread.authorize(credentials)
    sheet = gc.open('Medicart_lookup').worksheet('Withdrawal_history') 
    datentime = str(datetime.now())
    # Define the data for the new row
    new_row = [datentime, a, str(ls1), str(ls2)]  # Adjust these values as needed
    # Append the new row to the end of the sheet
    sheet.append_row(new_row)
    return(ls1, ls2)

def slotassign(list1, list2):
    displist = []
    comblist = []
    na = []
    narem =[]
    global rowsdata
    item_name = [row['Medicine'] for row in rowsdata[1:]]  # Assuming item name is in the first column
    avail_quantity = [row['Quantity'] for row in rowsdata[1:]]   # Availability in the third column
    avail_slot = [row['Machine_1 slot'] for row in rowsdata[1:]]  # Slot in the fourth column
    comb_slot = [row['Combination'] for row in rowsdata[1:]]  # Combined slot in the sixth column
    print(item_name, avail_quantity, avail_slot, comb_slot, list1)

    # Process list1 and list2 to assign slots
    for i in range(0, len(list1)):
        for j in range(0, int(list2[i])):
            for z in range(0, len(item_name)):
                if list1[i] == item_name[z] and int(avail_quantity[z])>0:
                    displist.append(str(avail_slot[z])) 
                elif list1[i] == item_name[z] and int(avail_quantity[z])==0:
                    comblist.append(str(comb_slot[z]))
                    na.append(list1[i]) 
    for k in range(0, len(comblist)):
        for l in range(0, len(comb_slot)):
             if comb_slot[l] == comblist[k] and int(avail_quantity[l])>0:
                 displist.append(str(avail_slot[l]))
                 narem.append(k)
    new_list = [value for index, value in enumerate(na) if index not in narem]
    print(displist)
    return(displist, new_list)

                    
            

    


def totalcost(a):
    global rowsdata
    cost = 0
    # Extract the necessary columns from rowsdata
    # Assuming column 4 has the items and column 7 has the cost
    slot = [row['Machine_1 slot'] for row in rowsdata[1:]]  # Skip header, adjust indexes as needed
    amt = [row['Amount'] for row in rowsdata[1:]]
    #print(slot, amt)
    # Iterate over each item in 'a'
    for item in a:
        for i in range(0, len(slot)):
            if int(item) == slot[i] and slot[i] != 0:
                #print(item, cost)
                cost = cost + int(amt[i])
    return cost


   
def checkavail(list1):
    global rowsdata
    availist = []
    first_column_values = [row['Medicine'] for row in rowsdata[1:]]  # Skip the header row, if it exists
    quantity = [row['Quantity'] for row in rowsdata[1:]]
    # Iterate over each value in list1
    for i in range(0,len(list1)):
        if list1[i] in first_column_values:
            # Get the index of the medicine in the first column
            row_index = first_column_values.index(list1[i])
            # Fetch the availability value from the third column of the matching row
            availability_value = quantity[row_index]  # Adjust index for zero-based list and header
            
            availist.append(availability_value)
            # If needed to update, can do so here by altering rowsdata directly
    return availist

def medstring_format(medlist):
    print(medlist)
    med = []
    quan = []
    print(medlist)
    
    for item in medlist:
        templist2 = item.split('.')
        med.append(templist2[0])
        quan.append(templist2[1])
    print(med, quan)
    return(med, quan)

def stringsep(data):
    templist1 = data.split(",")
    patient_name = templist1[1][10::]
    phone = templist1[3][10::]
    medicine_1 = templist1[4][12::]
    medlist = templist1[5:-1]
    medlist.append(medicine_1)
    ID = data[-6:]
    print(data)
    print(patient_name, medlist, phone, ID)
    return(patient_name, medlist, phone, ID)

def cam():    
    camera = cv2.VideoCapture(0)    
    global cam_done, qrinfo
    cam_done = False  # Ensure camera starts processing
    try:
        while True:
            ret, frame = camera.read()
            if not ret or cam_done:  # Check if the camera read was successful or if we should stop processing
                break  # Exit the loop if the camera read fails or if processing should stop
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(gray)
            for barcode in barcodes:
                barcodeData = barcode.data.decode()
                barcodeType = barcode.type
                qrdata = "{}".format(barcodeData)
                cam_done = True  # Indicate processing is done
                qrinfo = qrdata  # Return the decoded QR data            
            #cv2.imshow('camera feed', frame)            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        camera.release()  # Release the camera
        cv2.destroyAllWindows()  # Close all OpenCV windows
        #cam_done = True  # Ensure flag is set to True to indicate processing is complete
    
    
@app.route('/')
def start():
    qrinfo = ''
    return render_template('Start.html')

@app.route('/start-cam', methods=['POST'])
def start_cam():
    global cam_done
    cam_done = False  # Reset cam function state
    # Start cam function in a separate thread so it doesn't block
    Thread(target=cam).start()
    return redirect(url_for('scanning'))

@app.route('/scanning')
def scanning():
    return render_template('scanning.html')

@app.route('/check-cam')
def check_cam():
    return jsonify({'done': cam_done})

@app.route('/otp')
def otp():
    global rowsdata, qrinfo, p_name, mqlist, phone, ID, med, quan, disquan, displist, nalist 
    sheet = gc.open('Medicart_lookup').worksheet('Availability')
    rowsdata = sheet.get_all_records()
    p_name = "" 
    mqlist = []
    phone = ""
    ID = ""
    med = []
    quan = []
    disquan = []
    displist = []
    nalist = []
    p_name, mqlist, phone, ID = stringsep(qrinfo)
    #print(mqlist)
    
    id_stat = check_id(ID)
    #print(id_stat)
    if id_stat == "Completed":
        mqlist = []
    elif id_stat != "Fresh" and id_stat != "Completed":
        actual_list = ast.literal_eval(id_stat)
        mqlist = actual_list
    #print(mqlist)
    verified_number = "+91" + phone
    client = Client(account_sid, auth_token)
    verification=client.verify.v2.services(verify_sid) \
        .verifications \
        .create(to=verified_number, channel='sms')
    #print(verification.status)
    return render_template('OTP.html')

@app.route('/one_time_password', methods=['POST'])
def otp_check():
    global phone
    
    verified_number = "+91" + phone
    data = request.json
    otp_code = data.get('otp')
    #print("Received OTP:", otp_code)
    client = Client(account_sid, auth_token)
    verification_check = client.verify.v2.services(verify_sid) \
        .verification_checks \
        .create(to=verified_number, code=otp_code)
    stat = verification_check.status
    #print(stat)
    if stat == 'approved':
        return jsonify({'status': 'approved'})
    else:
        return jsonify({'status': 'denied'})
    
@app.route('/infopage')
def infopage():
    global mqlist, med, quan, disquan, displist, nalist
    med, quan = medstring_format(mqlist)
    availist = checkavail(med)
    print(availist, quan, med)
    for i in range(0,len(quan)):
        disquan.append(min(int(quan[i]), int(availist[i])))        
    return render_template('infopage.html', list1=med, list2=disquan, zip=zip)

@app.route('/payment')
def payment():
    global med, quan, displist, nalist
    displist, nalist = slotassign(med, quan)
    cost = totalcost(displist)
    amount = str(cost)
    upi_id = 'suriyamanivasagan12@oksbi'
    payment_string = f"upi://pay?pa={upi_id}&pn=RecipientName&am={amount}"
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Save QR code to a BytesIO buffer
    img_buffer = BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)
    # Encode image to data URL
    img_data = img_buffer.getvalue()
    data_uri = 'data:image/png;base64,' + b64encode(img_data).decode('utf-8')
    return render_template('payment.html', qr_data=data_uri,amount=amount)
    
@app.route('/update')
def updatedb():
    global disp_done, p_name, mqlist, phone, ID, displist, nalist
    disp_done = False
    print(displist)
    ls1, ls2 = withdraw_update(p_name, mqlist)
    availupdate(displist)
    if len(ls1) <= len(displist):
        id_update(ID, "Completed")
    else :
        str1 = "["
        for i in range(0, len(nalist)):
            if i>0: str1 = str1 + ","
            str1 = str1 + "'" + nalist[i] + ".1'"
        str1 = str1 + "]"
        id_update(ID,str1)
    Thread(target=dispense, args=(displist,)).start()
    return redirect(url_for('finish'))
    
@app.route('/finish')
def finish():
    return render_template('dispense.html')
    
@app.route('/check-disp')
def check_disp():
    print(disp_done)
    return jsonify({'done': disp_done})
    
@app.route('/thank')
def thank():
    return render_template('thank.html')

if __name__ == '__main__':
    app.run(debug=True)


