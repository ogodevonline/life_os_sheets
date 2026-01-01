from life_os import LifeOS

def main():
    life_os = LifeOS()
    life_os.create_spreadsheet()
    life_os.build_sheets()

    print("✅ Life OS v3.0 готова! Масштабируйся до 20 лет вперед.")
    print(f"🔗 Ссылка: {life_os.get_url()}")

if __name__ == "__main__":
    main() 