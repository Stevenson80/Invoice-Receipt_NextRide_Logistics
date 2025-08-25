import os


def create_templates_folder():
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print("Created templates directory")

    # Create index.html file
    index_html_path = os.path.join(templates_dir, 'index.html')

    index_html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NextRide Logistics - Invoice & Receipt Generator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1, h2 {
            color: #3498db;
        }
        .form-section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #2980b9;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: #eee;
            cursor: pointer;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
        }
        .tab.active {
            background: #3498db;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>NextRide Logistics - Invoice & Receipt Generator</h1>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('invoice')">Generate Invoice</div>
            <div class="tab" onclick="switchTab('receipt')">Generate Receipt</div>
        </div>

        <div id="invoice-tab" class="tab-content active">
            <h2>Generate Invoice</h2>
            <form action="/generate_invoice" method="post">
                <div class="form-section">
                    <h3>Client Information</h3>
                    <div class="form-group">
                        <label for="client_name">Client Name:</label>
                        <input type="text" id="client_name" name="client_name" required>
                    </div>
                    <div class="form-group">
                        <label for="client_address">Client Address:</label>
                        <input type="text" id="client_address" name="client_address" required>
                    </div>
                    <div class="form-group">
                        <label for极client_contact">Client Contact:</label>
                        <input type="text" id="client_contact" name="client_contact" required>
                    </div>
                </div>

                <div class="form-section">
                    <h3>Trip Details</h3>
                    <div class="form-group">
                        <label for="trip_type">Trip Type:</label>
                        <select id="trip_type" name="trip_type" required onchange="toggleReturnDate()">
                            <option value="Single Trip">Single Trip</option>
                            <option value="Round Trip">Round Trip</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="pickup_point">Pickup Point:</label>
                        <input type="text" id="pickup_point" name="pickup_point" required>
                    </div>
                    <div class="form-group">
                        <label for="dropoff_point">Drop Off Point:</label>
                        <input type="text" id="dropoff_point" name="dropoff_point" required>
                    </div>
                    <极 class="form-group">
                        <label for="trip_date">Trip Date:</label>
                        <input type="date" id="trip_date" name="trip_date" required>
                    </div>
                    <div class="form-group" id="return_date_group" style="display: none;">
                        <label for="return_date">Return Date:</label>
                        <input type="date" id="return_date" name="return_date">
                    </div>
                </div>

                <div class="form-section">
                    <h3>Service Details</h3>
                    <div class="form-group">
                        <label for="description">Service Description:</label>
                        <textarea id="description" name="description" rows="3" required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="quantity">Quantity:</label>
                        <input type="number" id="quantity" name="quantity" value="1" min="1" required>
                    </div>
                    <div class="form-group">
                        <label for="price">Price (₦):</label>
                        <input type="number" id="price" name="price" step="0.01" min="0" required>
                    </div>
                </div>

                <div class="form-section">
                    <h3>Additional Notes</h3>
                    <div class="form-group">
                        <textarea id="notes" name极notes" rows="3"></textarea>
                    </div>
                </div>

                <button type="submit">Generate Invoice PDF</button>
            </form>
        </div>

        <div id="receipt-tab" class="tab-content">
            <h2>Generate Receipt</h2>
            <form action="/generate_receipt" method="post">
                <div class="form-section">
                    <h3>Client Information</h3>
                    <div class="form-group">
                        <label for="receipt_client_name">Client Name:</label>
                        <input type="text" id="receipt_client_name" name="client_name" required>
                    </div>
                    <div class="form-group">
                        <label for="receipt_client_address">Client Address:</label>
                        <input type="text" id="receipt_client_address" name="client_address" required>
                    </div>
                    <div class="form-group">
                        <label for="receipt_client_contact">Client Contact:</label>
                        <input type="text" id="receipt_client_contact" name="client_contact" required>
                    </div>
                </div>

                <div class="form-section">
                    <h3>Payment Details</h3>
                    <div class="form-group">
                        <label for="receipt_description">Service Description:</label>
                        <textarea id="receipt_description" name="description" rows="3" required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="amount_paid">Amount Paid (₦):</label>
                        <input type="number" id="amount_paid" name="amount_paid" step="0.01" min="0" required>
                    </div>
                    <div class="form-group">
                        <label for="payment_method">Payment Method:</label>
                        <select id="payment_method" name="payment_method" required>
                            <option value="Cash">Cash</option>
                            <option value="Bank Transfer">Bank Transfer</option>
                            <option value="POS">POS</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                </div>

                <div class="form-section">
                    <h3>Additional Notes</h3>
                    <div class="form-group">
                        <textarea id="receipt_notes" name="notes" rows="3"></textarea>
                    </div>
                </div>

                <button type="submit">Generate Receipt PDF</button>
            </form>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');

            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
        }

        function toggleReturnDate() {
            const tripType = document.getElementById('trip_type').value;
            const returnDateGroup = document.getElementById('return_date_group');

            if (tripType === 'Round Trip') {
                returnDateGroup.style.display = 'block';
            } else {
                returnDateGroup.style.display = 'none';
            }
        }
    </script>
</body>
</html>'''

    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(index_html_content)

    print("Created index.html file")

    return templates_dir, index_html_path


if __name__ == "__main__":
    create_templates_folder()