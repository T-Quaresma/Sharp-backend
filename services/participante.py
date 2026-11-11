from database import db
from models import ParticipantesAtiv, Usuario, Agendamento, Atividade

# send invitation to a user to participate in a schedule

def add_participant(data, user_id):
    schedule = db.session.execute(
        db.select(Agendamento).where(
            Agendamento.agenId == data.schedule_id
        )
    ).scalars().first()
    if schedule is None:
        return {
            "Message": "Schedule not found."
        }, 404
    if schedule.atividade.criadorId != user_id:
        return {
            "Message": "You do not have permission to add participants to this schedule."
        }, 403
    if data.user_id == user_id:
        return {
            "Message": "You cannot add yourself as a participant."
        }, 400
    participant_user = db.session.execute(
        db.select(Usuario).where(
            Usuario.usuId == data.user_id
        )
    ).scalars().first()
    if participant_user is None:
        return {
            "Message": "User not found."
        }, 404
    existing_participant = db.session.execute(
        db.select(ParticipantesAtiv).where(
            ParticipantesAtiv.usuId == data.user_id,
            ParticipantesAtiv.agenId == data.schedule_id
        )
    ).scalars().first()
    if existing_participant is not None:
        return {
            "Message": "An invitation already exists for this user and schedule.",
            "status": existing_participant.status
        }, 409
    new_participant = ParticipantesAtiv(
        usuId=data.user_id,
        agenId=data.schedule_id,
        status="pending"
    )
    db.session.add(new_participant)
    db.session.commit()
    return {
        "Message": "Invitation sent successfully.",
        "partId": new_participant.partId,
        "status": new_participant.status
    }, 201

# accept or decline an invitation to participate in a schedule

def respond_to_invitation(data, user_id):
    invitation = db.session.execute(
        db.select(ParticipantesAtiv).where(
            ParticipantesAtiv.partId == data.id
        )
    ).scalars().first()
    if invitation is None:
        return {
            "Message": "Invitation not found;"
        }, 404
    if invitation.usuId != user_id:
        return {
            "Message": "You do not have permission to respond to this invitation."
        }, 403
    if invitation.status != "pending":
        return {
            "Message": "This invitation has already been answered."
        }, 409
    invitation.status = data.status
    db.session.commit()
    return {
        "Message": f"Invitation {data.status} successfully.",
        "partId": invitation.partId,
        "status": invitation.status
    }, 200

# list all participants of a schedule, only the creator of the schedule can do this

def select_participant(data, user_id):
    schedule = db.session.execute(
        db.select(Agendamento).where(
            Agendamento.agenId == data.schedule_id
        )
    ).scalars().first()
    if schedule is None:
        return {
            "Message": "Schedule not found."
        }, 404
    if schedule.atividade.criadorId != user_id:
        return {
            "Message": "You do not have permission to view participants from this schedule."
        }, 403
    participants = db.session.execute(
        db.select(ParticipantesAtiv)
        .where(
            ParticipantesAtiv.agenId == data.schedule_id
        )
    ).scalars().all()
    participant_list = []
    for participant in participants:
        participant_list.append({
            "nomeUsu": participant.usuario.nomeUsu,
            "usuId": participant.usuario.usuId,
            "partId": participant.partId,
            "status": participant.status
        })
    return participant_list, 200

# remove a participant from a schedule, only the creator of the schedule can do this

def delete_participant(data, user_id):
    participant = db.session.execute(
        db.select(ParticipantesAtiv).where(
            ParticipantesAtiv.partId == data.id
        )
    ).scalars().first()
    if participant is None:
        return {
            "Message": "Participant not found."
        }, 404
    schedule = db.session.execute(
        db.select(Agendamento).where(
            Agendamento.agenId == participant.agenId
        )
    ).scalars().first()
    if schedule is None:
        return {
            "Message": "Schedule not found."
        }, 404
    if schedule.atividade.criadorId != user_id:
        return {
            "Message": "You do not have permission to remove this participant."
        }, 403
    db.session.delete(participant)
    db.session.commit()
    return {
        "Message": "Participant removed successfully."
    }, 200

# List all received invitations for a user

def list_received_invitations(user_id):
    invitations = db.session.execute(
        db.select(ParticipantesAtiv).where(
        ParticipantesAtiv.usuId == user_id,
        ParticipantesAtiv.status == "pending"
        )
    ).scalars().all()

    invitation_list = []

    for invitation in invitations:
        schedule = invitation.agendamento
        activity = schedule.atividade
        invitation_list.append({
            "partId": invitation.partId,
            "schedule_id": schedule.agenId,
            "activity_id": activity.ativId,
            "status": invitation.status
        })
    return invitation_list, 200


def leave_schedule(data, user_id):
    participant = db.session.execute(
        db.select(ParticipantesAtiv).where(
            ParticipantesAtiv.usuId == user_id,
            ParticipantesAtiv.agenId == data.schedule_id
        )
    ).scalars().first()

    if participant is None:
        return {
            "Message": "You are not a participant of this schedule."
        }, 404

    if participant.status != "accepted":
        return {
            "Message": "You can only leave a schedule after accepting its invitation."
        }, 409

    db.session.delete(participant)
    db.session.commit()

    return {
        "Message": "You have successfully left the schedule."
    }, 200

