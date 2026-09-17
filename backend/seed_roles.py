import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine, Base
from app.models.models import User
from app.core.security import hash_password

# Ensure tables exist (important for fresh Postgres on Render)
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    seed_data = [
        {
            'username': 'boss',
            'full_name': 'Сапарбаев Нұрлан Болатұлы',
            'role': 'BOSS',
            'position': 'ПЧ Бастығы (Директор)',
            'organization': 'ПЧ-13 (Алматы дистанциясы)',
            'unit_code': 'ПЧ-13',
            'subdivision': 'Бас басқарма',
            'iin': '780315301980',
            'emp_num': 'Т-0001',
            'password': 'boss',
            'phone': '+7 (777) 111-22-33'
        },
        {
            'username': 'dispatcher',
            'full_name': 'Әлімжанов Асқар Серікұлы',
            'role': 'DISPATCHER',
            'position': 'Поезд Диспетчері (ДНЦ)',
            'organization': 'ПЧ-13 (Алматы дистанциясы)',
            'unit_code': 'ПЧ-13',
            'subdivision': 'Диспетчерлік орталық',
            'iin': '820421302450',
            'emp_num': 'Т-0002',
            'password': 'dispatcher',
            'phone': '+7 (777) 222-33-44'
        },
        {
            'username': 'master',
            'full_name': 'Серіков Мұрат Қанатұлы',
            'role': 'MASTER',
            'position': 'Жол шебері (Участок №3)',
            'organization': 'ПЧ-13 (Алматы дистанциясы)',
            'unit_code': 'ПЧ-13',
            'subdivision': 'Участок №3, Околоток №10',
            'iin': '860710303120',
            'emp_num': 'Т-0003',
            'password': 'master',
            'phone': '+7 (777) 333-44-55'
        },
        {
            'username': 'worker',
            'full_name': 'Бақытов Дәулет Нұржанұлы',
            'role': 'WORKER',
            'position': 'Монтер пути 4-разряда',
            'organization': 'ПЧ-13 (Алматы дистанциясы)',
            'unit_code': 'ПЧ-13',
            'subdivision': 'Участок №3, Околоток №10',
            'iin': '950912304890',
            'emp_num': 'Т-0004',
            'password': 'worker',
            'phone': '+7 (777) 444-55-66'
        }
    ]

    for item in seed_data:
        u = db.query(User).filter(User.username == item['username']).first()
        if not u:
            new_u = User(
                username=item['username'],
                password_hash=hash_password(item['password']),
                full_name=item['full_name'],
                role=item['role'],
                position=item['position'],
                organization=item['organization'],
                unit_code=item['unit_code'],
                subdivision=item['subdivision'],
                iin=item['iin'],
                emp_num=item['emp_num'],
                phone=item['phone'],
                email=item['username'] + "@railways.kz"
            )
            db.add(new_u)
            print("Created: " + item['username'] + " (" + item['role'] + ")")
        else:
            print("Already exists: " + item['username'])

    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
