# from sqlalchemy.orm import Session
# from database import SessionLocal
# import models
#
# def seed_data():
#     db: Session = SessionLocal()
#
#     # Step 2: Insert Users
#     users = [
#         models.Users(name="Alice Wong", email="alice@example.com"),
#         models.Users(name="Ben Carter", email="ben@example.com"),
#         models.Users(name="Clara Smith", email="clara@example.com"),
#     ]
#     db.add_all(users)
#     db.commit()
#
#     for user in users:
#         db.refresh(user)
#
#     # Step 3: Insert Sources
#     sources = [
#         models.Sources(name="JobBoardPro", base_url="https://jobboardpro.com"),
#         models.Sources(name="CareerHub", base_url="https://careerhub.io"),
#     ]
#     db.add_all(sources)
#     db.commit()
#
#     # Step 4: Insert Listings
#     listings = [
#         models.Listings(
#             title="Junior Python Developer",
#             description="Entry-level dev role for Python + FastAPI apps",
#             price=0,
#             source_id=1,
#
#         ),
#         models.Listings(
#             title="Senior Data Engineer",
#             description="Build scalable ETL pipelines",
#             price=0,
#             source_id=1,
#
#         ),
#         models.Listings(
#             title="AWS Cloud Specialist",
#             description="Manage AWS RDS and Lambda deployments",
#             price=0,
#             source_id=2,
#
#         ),
#         models.Listings(
#             title="UI/UX Designer",
#             description="Design modern, responsive web apps",
#             price=0,
#             source_id=2,
#
#         ),
#         models.Listings(
#             title="DevOps Engineer",
#             description="CI/CD pipelines, Kubernetes, Terraform",
#             price=0,
#             source_id=1,
#
#         ),
#         models.Listings(
#             title="Database Administrator",
#             description="Maintain Postgres, monitor performance",
#             price=0,
#             source_id=2,
#
#         )
#     ]
#     db.add_all(listings)
#     db.commit()
#
#     db.close()
#
# if __name__ == "__main__":
#     seed_data()
