"""
Test Data Generator for Property Blockchain
Run this script to populate the blockchain with sample data for testing.
"""

import random
from datetime import datetime
from blockchain import PropertyBlockchain

# Sample data pools
FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Sunita", "Vikram", "Kavita", "Arun", "Meera",
    "Suresh", "Anita", "Ramesh", "Deepa", "Mahesh", "Lakshmi", "Ganesh", "Radha",
    "Sanjay", "Pooja", "Vijay", "Neha", "Ravi", "Sita", "Krishna", "Gita",
    "Dinesh", "Sarika", "Naresh", "Manjula", "Prakash", "Usha", "Kishore", "Indira",
    "Mohan", "Parvati", "Ashok", "Savitri", "Harish", "Kamala", "Satish", "Vimala",
    "Gopal", "Shanta", "Bhaskar", "Prema", "Mukesh", "Sumitra", "Naveen", "Rekha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Rao", "Nair", "Menon",
    "Gupta", "Verma", "Joshi", "Iyer", "Pillai", "Das", "Chatterjee", "Banerjee",
    "Desai", "Shah", "Mehta", "Kapoor", "Malhotra", "Khanna", "Bose", "Sen",
    "Naik", "Kulkarni", "Shukla", "Mishra", "Tiwari", "Pandey", "Agarwal", "Jain",
    "Sethi", "Chopra", "Bhatia", "Sinha", "Mukherjee", "Roy", "Ghosh", "Dutta"
]

VILLAGES = [
    "Chandpur", "Rampur", "Krishnanagar", "Lakshmipur", "Gopalpur", "Srinagar",
    "Rajapur", "Shankarpur", "Vishnupur", "Shivapur", "Nagpur", "Mathurapur",
    "Devipur", "Hanumanpur", "Kalipur", "Balaji Nagar", "Anantpur", "Kamalpur"
]

TALUKS = [
    "North Taluk", "South Taluk", "East Taluk", "West Taluk", "Central Taluk",
    "Urban Taluk", "Rural Taluk", "Coastal Taluk", "Hill Taluk", "Valley Taluk"
]

DISTRICTS = [
    "Bangalore Urban", "Mumbai Suburban", "Chennai Central", "Hyderabad", "Pune", "Kolkata",
    "Delhi", "Jaipur", "Lucknow", "Ahmedabad", "Surat", "Indore", "Bhopal", "Nagpur",
    "Visakhapatnam", "Coimbatore", "Kochi", "Trivandrum", "Mysore", "Mangalore"
]

STATES = [
    "Karnataka", "Maharashtra", "Tamil Nadu", "Telangana", "West Bengal", "Gujarat",
    "Rajasthan", "Uttar Pradesh", "Madhya Pradesh", "Kerala", "Andhra Pradesh", "Delhi"
]

LAND_TYPES = ["Residential", "Commercial", "Agricultural", "Industrial"]

STREETS = [
    "MG Road", "Gandhi Street", "Nehru Lane", "Patel Nagar", "Rajaji Road",
    "Subhash Chowk", "Ambedkar Avenue", "Sardar Patel Marg", "Tilak Road",
    "Lal Bahadur Street", "Indira Gandhi Road", "Tagore Circle", "Vivekananda Path",
    "JP Nagar", "Anna Salai", "Brigade Road", "Commercial Street", "Church Street"
]


def generate_aadhar():
    """Generate a valid 12-digit Aadhar number"""
    return ''.join([str(random.randint(0, 9)) for _ in range(12)])


def generate_pan():
    """Generate a valid PAN number (format: ABCDE1234F)"""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return (
        ''.join(random.choices(letters, k=5)) +
        ''.join([str(random.randint(0, 9)) for _ in range(4)]) +
        random.choice(letters)
    )


def generate_survey_number():
    """Generate a survey number in Indian format"""
    formats = [
        lambda: str(random.randint(100000, 999999)),  # Whole parcel: e.g., 150789
        lambda: f"{random.randint(10, 999)}/{random.randint(1, 99)}",  # Subdivided: e.g., 24/1, 42/2
        lambda: f"{random.randint(10, 999)}/{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",  # Subdivided: e.g., 10/A
        lambda: f"Khasra No {random.randint(100, 999)}",  # Khasra: e.g., Khasra No 105
    ]
    return random.choice(formats)()


def generate_property_key():
    """Generate a unique property key"""
    return f"PROP-{random.randint(10000, 99999)}-{random.randint(100, 999)}"


def generate_pincode():
    """Generate a valid 6-digit pincode"""
    return str(random.randint(100000, 999999))


def generate_address():
    """Generate a random property address"""
    plot = random.randint(1, 500)
    street = random.choice(STREETS)
    return f"Plot No. {plot}, {street}"


def generate_person():
    """Generate a random person with valid Indian identity"""
    return {
        "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "aadhar": generate_aadhar(),
        "pan": generate_pan()
    }


def main():
    print("=" * 60)
    print("🏠 Property Blockchain - Test Data Generator")
    print("=" * 60)
    
    # Initialize blockchain
    blockchain = PropertyBlockchain(verbose=True)
    
    print(f"\n📊 Current blockchain status:")
    print(f"   Total blocks: {len(blockchain.chain)}")
    chain_info = blockchain.get_chain_info()
    print(f"   Total properties: {chain_info.get('total_properties', 0)}")
    
    # Ask user how many properties to generate
    try:
        num_input = input("\n🔢 How many properties to generate? (default: 30): ").strip()
        num_properties = int(num_input) if num_input else 30
        if num_properties < 1:
            print("   ⚠️  Invalid number, using default 30")
            num_properties = 30
        elif num_properties > 100:
            print("   ⚠️  Too many! Limited to 100 properties")
            num_properties = 100
    except ValueError:
        print("   ⚠️  Invalid input, using default 30")
        num_properties = 30
    
    print(f"\n🔨 Generating {num_properties} test properties...\n")
    
    registered_properties = []
    
    for i in range(num_properties):
        owner = generate_person()
        property_key = generate_property_key()
        survey_no = generate_survey_number()
        
        property_data = {
            "property_key": property_key,
            "survey_no": survey_no,
            "owner_name": owner["name"],
            "owner_aadhar": owner["aadhar"],
            "owner_pan": owner["pan"],
            "address": generate_address(),
            "pincode": generate_pincode(),
            "value": random.randint(500000, 10000000),
            "village": random.choice(VILLAGES),
            "taluk": random.choice(TALUKS),
            "district": random.choice(DISTRICTS),
            "state": random.choice(STATES),
            "land_area": f"{random.randint(500, 5000)} sq.ft",
            "land_type": random.choice(LAND_TYPES)
        }
        
        print(f"📝 Registering Property {i + 1}:")
        print(f"   Key: {property_data['property_key']}")
        print(f"   Survey: {property_data['survey_no']}")
        print(f"   Owner: {property_data['owner_name']}")
        print(f"   Location: {property_data['village']}, {property_data['district']}")
        print(f"   Area: {property_data['land_area']}")
        print(f"   Value: ₹{property_data['value']:,}")
        
        try:
            block = blockchain.add_property(
                property_key=property_data["property_key"],
                owner=property_data["owner_name"],
                address=property_data["address"],
                pincode=property_data["pincode"],
                value=property_data["value"],
                aadhar_no=property_data["owner_aadhar"],
                pan_no=property_data["owner_pan"],
                survey_no=property_data["survey_no"],
                village=property_data["village"],
                taluk=property_data["taluk"],
                district=property_data["district"],
                state=property_data["state"],
                land_area=property_data["land_area"],
                land_type=property_data["land_type"]
            )
            registered_properties.append(property_data)
            print(f"   ✅ Successfully registered! Block #{block.index}\n")
        except ValueError as e:
            print(f"   ❌ Failed: {str(e)}\n")
    
    # Simulate property transfers (30% of properties)
    num_transfers = max(1, int(len(registered_properties) * 0.3))
    if len(registered_properties) >= 2:
        print(f"\n🔄 Simulating {num_transfers} property transfers...\n")
        
        transfer_indices = random.sample(range(len(registered_properties)), min(num_transfers, len(registered_properties)))
        
        for idx in transfer_indices:
            prop = registered_properties[idx]
            new_owner = generate_person()
            
            print(f"📤 Transferring property {idx + 1}:")
            print(f"   Property: {prop['property_key']}")
            print(f"   From: {prop['owner_name']}")
            print(f"   To: {new_owner['name']}")
            
            try:
                block = blockchain.transfer_property(
                    property_key=prop["property_key"],
                    new_owner=new_owner["name"],
                    new_owner_aadhar=new_owner["aadhar"],
                    new_owner_pan=new_owner["pan"],
                    transfer_value=prop["value"] + random.randint(50000, 500000),
                    transfer_reason="sale"
                )
                print(f"   ✅ Transfer completed! Block #{block.index}")
                # Update the registered property info
                prop["owner_name"] = new_owner["name"]
                prop["owner_aadhar"] = new_owner["aadhar"]
                prop["owner_pan"] = new_owner["pan"]
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
            print()
    
    # Perform inheritances (10% of properties)
    num_inheritances = max(1, int(len(registered_properties) * 0.1))
    if len(registered_properties) >= 3:
        print(f"\n👨‍👩‍👧 Simulating {num_inheritances} property inheritances...\n")
        
        # Select properties that haven't been transferred
        available_for_inheritance = [p for p in registered_properties if p not in [registered_properties[i] for i in transfer_indices[:num_transfers]]]
        inheritance_props = random.sample(available_for_inheritance, min(num_inheritances, len(available_for_inheritance)))
        
        for prop in inheritance_props:
            heir = generate_person()
            
            print(f"📜 Inheriting property:")
            print(f"   Property: {prop['property_key']}")
            print(f"   From: {prop['owner_name']}")
            print(f"   To (Heir): {heir['name']}")
            
            try:
                block = blockchain.transfer_property(
                    property_key=prop["property_key"],
                    new_owner=heir["name"],
                    new_owner_aadhar=heir["aadhar"],
                    new_owner_pan=heir["pan"],
                    transfer_value=prop["value"],
                    transfer_reason="inheritance"
                )
                print(f"   ✅ Inheritance recorded! Block #{block.index}")
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
            print()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    successful_properties = len([p for p in registered_properties if p])
    print(f"   Total Blocks: {len(blockchain.chain)}")
    print(f"   Properties Registered: {successful_properties}")
    print(f"   Transfers Completed: {num_transfers if len(registered_properties) >= 2 else 0}")
    print(f"   Inheritances Recorded: {num_inheritances if len(registered_properties) >= 3 else 0}")
    print(f"   Total Transactions: {len(blockchain.chain) - 1}")  # Excluding genesis block
    
    # Validate blockchain
    is_valid, message = blockchain.is_valid()
    print(f"\n   Blockchain Valid: {'✅ Yes' if is_valid else '❌ No'}")
    print(f"   Validation: {message}")
    
    # Save blockchain to encrypted storage
    print("\n💾 Saving blockchain to encrypted storage...")
    blockchain.save_and_exit()
    print("   ✅ Blockchain saved successfully!")
    print("\n🎉 Test data generation complete!")
    print("\n⚠️  IMPORTANT: If Flask app is running, RESTART it to see the new data!")
    print("   1. Stop the Flask app (Ctrl+C)")
    print("   2. Start it again: python app.py")
    print("   3. Refresh your browser to see the updated properties")
    print("=" * 60)


if __name__ == "__main__":
    main()
