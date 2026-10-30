from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Named unique constraints: constraint_errors.py maps each name to its domain error.
PROFILE_USER_KEY = 'owner_profiles_user_uuid_key'
PROFILE_RUC_KEY = 'owner_profiles_ruc_key'
DOCUMENT_KEY = 'identity_documents_document_type_document_number_key'
DEFAULT_DOCUMENT_KEY = 'identity_documents_owner_profile_uuid_default_key'


class Base(DeclarativeBase):
    pass


class OwnerProfileModel(Base):
    __tablename__ = 'owner_profiles'
    __table_args__ = (
        UniqueConstraint('user_uuid', name=PROFILE_USER_KEY),
        UniqueConstraint('ruc', name=PROFILE_RUC_KEY),
    )

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column()
    ruc: Mapped[str] = mapped_column(String(11))
    address: Mapped[str | None] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Saved with the profile in the same flush (the documents are part of its aggregate).
    identity_documents: Mapped[list['IdentityDocumentModel']] = relationship(
        lazy='raise'
    )


class IdentityDocumentModel(Base):
    __tablename__ = 'identity_documents'
    __table_args__ = (
        UniqueConstraint('document_type', 'document_number', name=DOCUMENT_KEY),
        Index(
            DEFAULT_DOCUMENT_KEY,
            'owner_profile_uuid',
            unique=True,
            postgresql_where=text('is_default'),
        ),
    )

    uuid: Mapped[UUID] = mapped_column(primary_key=True)
    owner_profile_uuid: Mapped[UUID] = mapped_column(ForeignKey('owner_profiles.uuid'))
    document_type: Mapped[str] = mapped_column(String(20))
    document_number: Mapped[str] = mapped_column(String(15))
    is_default: Mapped[bool] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
