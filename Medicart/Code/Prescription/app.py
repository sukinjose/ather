import qrcode
from flask import Flask, request, render_template, send_file
from io import BytesIO
from base64 import b64encode
import random

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/process_medicine_data', methods=['POST'])
@app.route('/process_medicine_data', methods=['POST'])
def process_medicine_data():

    doctor_name = request.form.get('doctor_name')
    patient_name = request.form.get('patient_name')
    doctor_pin = request.form.get('doctor_pin')
    phone_num = request.form.get('phone_num')
    Pres_ID = random.randint(100000, 999999)
    # Process the medicine data
    medicine_data = []
    for i in range(1, 5):
        medicine_name = request.form.get(f'medicine_{i}_name')
        quantity = request.form.get(f'medicine_{i}_quantity')
        if medicine_name and quantity:  # Ensure both fields are provided
            medicine_data.append((medicine_name, quantity))

    # Combine all data into a single string
    medicine_data_str = ','.join([f'{name}.{qty}' for name, qty in medicine_data])
    final_str = f'Doctor: {doctor_name}, Patient: {patient_name}, PIN: {doctor_pin}, Number : {phone_num}, Medicines: {medicine_data_str}, ID: {Pres_ID}'
   

    # For demonstration, just printing the data
    print(final_str)
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(final_str)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code to a BytesIO buffer
    img_buffer = BytesIO()
    img.save(img_buffer)
    img_buffer.seek(0)

    # Encode image to data URL
    img_data = img_buffer.getvalue()
    data_uri = 'data:image/png;base64,' + b64encode(img_data).decode('utf-8')

    return render_template('qr_display.html', doctor_name=doctor_name, patient_name=patient_name, medicine_data=medicine_data, qr_data=data_uri)
    
    return "Medicine data processed successfully!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
