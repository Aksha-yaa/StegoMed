from PIL import Image
from cryptography.fernet import Fernet
import numpy as np
import matplotlib.pyplot as plt
import os

# AES Key management
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)

def load_key():
    if not os.path.exists("secret.key"):
        generate_key()
    return open("secret.key", "rb").read()

# AES encryption/decryption
def encrypt(data, key):
    cipher = Fernet(key)
    return cipher.encrypt(data.encode())

def decrypt(data, key):
    cipher = Fernet(key)
    return cipher.decrypt(data).decode()

# Display image
def show_image(image_path, title="Image"):
    try:
        img = Image.open(image_path)
        plt.imshow(img)
        plt.title(title)
        plt.axis('off')
        plt.show()
    except Exception as e:
        print(f"⚠️ Could not display image: {e}")

# Convert integer to 32-bit binary and back
def int_to_bin32(n):
    return format(n, '032b')

def bin32_to_int(bstr):
    return int(bstr, 2)

# LSB Encode with embedded length
def encode_lsb(image_path, encrypted_data, output_path):
    img = Image.open(image_path).convert("RGB")
    img_array = np.array(img)
    flat = img_array.flatten().tolist()

    data_len = len(encrypted_data)
    binary_length = int_to_bin32(data_len)  # first 32 bits
    binary_data = binary_length + ''.join(format(byte, '08b') for byte in encrypted_data)

    if len(binary_data) > len(flat):
        raise ValueError("Image too small to embed this data.")

    for i in range(len(binary_data)):
        flat[i] = (flat[i] & ~1) | int(binary_data[i])

    flat = [min(255, max(0, val)) for val in flat]
    encoded_array = np.array(flat, dtype=np.uint8).reshape(img_array.shape)
    encoded_img = Image.fromarray(encoded_array)
    encoded_img.save(output_path)
    print(f"\n✅ Image encoded and saved as '{output_path}'")
    show_image(output_path, title="Encrypted Image")

# LSB Decode with automated length extraction
def decode_lsb(image_path):
    flat = np.array(Image.open(image_path)).flatten()

    # Read first 32 bits for length
    length_bits = ''.join(str(flat[i] & 1) for i in range(32))
    length = bin32_to_int(length_bits)

    # Now extract encrypted data
    data_bits = ''.join(str(flat[32 + i] & 1) for i in range(length * 8))
    byte_data = [data_bits[i:i+8] for i in range(0, len(data_bits), 8)]
    return bytes([int(b, 2) for b in byte_data])

# Main menu
def main():
    key = load_key()

    while True:
        print("\n🩺 Stego Med Menu")
        print("1. Encrypt & Embed Patient Info")
        print("2. Extract & Decrypt Patient Info")
        print("3. Exit")

        choice = input("Choose an option: ")

        if choice == '1':
            try:
                image_path = input("\n🔍 Enter path to diagnostic image: ").strip()
                if not os.path.exists(image_path):
                    raise FileNotFoundError("Image not found.")

                show_image(image_path, title="Original Image")

                print("\n🧾 Enter Patient Info")
                name = input("Name: ")
                pid = input("Patient ID: ")
                age = input("Age: ")
                diagnosis = input("Diagnosis: ")
                doctor = input("Attending Physician: ")

                patient_record = f"Name:{name}, ID:{pid}, Age:{age}, Diagnosis:{diagnosis}, Physician:{doctor}"
                encrypted = encrypt(patient_record, key)

                output_path = input("📁 Enter path to save encrypted image (e.g., encrypted.png): ").strip()
                encode_lsb(image_path, encrypted, output_path)

            except Exception as e:
                print(f"⚠️ Error during encryption: {e}")

        elif choice == '2':
            try:
                image_path = input("\n📥 Enter path to encrypted image: ").strip()
                if not os.path.exists(image_path):
                    raise FileNotFoundError("Image not found.")

                hidden_data = decode_lsb(image_path)
                decrypted = decrypt(hidden_data, key)
                print(f"\n🔓 Decrypted Patient Info:\n{decrypted}")

                save_copy = input("\n💾 Do you want to save a copy of this image? (y/n): ").lower()
                if save_copy == 'y':
                    save_path = input("📁 Enter path to save the image: ").strip()
                    try:
                        img = Image.open(image_path)
                        img.save(save_path)
                        print(f"✅ Image saved at: {save_path}")
                    except Exception as e:
                        print(f"⚠️ Could not save image: {e}")

            except Exception as e:
                print(f"⚠️ Error during decryption: {e}")

        elif choice == '3':
            print("\n👋 Exiting Stego Med. Stay secure!")
            break

        else:
            print("🚫 Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
