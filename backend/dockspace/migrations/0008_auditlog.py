# Generated migration for AuditLog model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dockspace', '0007_appsettings_allow_registration'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('account.create', 'Account Created'), ('account.update', 'Account Updated'), ('account.delete', 'Account Deleted'), ('account.suspend', 'Account Suspended'), ('account.activate', 'Account Activated'), ('account.password_change', 'Password Changed'), ('alias.create', 'Alias Created'), ('alias.delete', 'Alias Deleted'), ('group.create', 'Group Created'), ('group.update', 'Group Updated'), ('group.delete', 'Group Deleted'), ('group.member_add', 'Member Added to Group'), ('group.member_remove', 'Member Removed from Group'), ('quota.create', 'Quota Created'), ('quota.update', 'Quota Updated'), ('quota.delete', 'Quota Deleted'), ('oidc.create', 'OIDC Client Created'), ('oidc.update', 'OIDC Client Updated'), ('oidc.delete', 'OIDC Client Deleted'), ('settings.update', 'Application Settings Updated'), ('settings.smtp_update', 'SMTP Settings Updated'), ('auth.login', 'User Login'), ('auth.logout', 'User Logout'), ('auth.login_failed', 'Login Failed'), ('auth.2fa_enabled', '2FA Enabled'), ('auth.2fa_disabled', '2FA Disabled'), ('session.created', 'Session Created'), ('session.terminated', 'Session Terminated')], help_text='Type of action performed', max_length=50)),
                ('target_type', models.CharField(blank=True, help_text="Type of object affected (e.g., 'MailAccount', 'MailGroup')", max_length=50)),
                ('target_id', models.IntegerField(blank=True, help_text='ID of the affected object', null=True)),
                ('target_name', models.CharField(blank=True, help_text='Human-readable name of the affected object', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Human-readable description of what happened')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional structured data about the action (changes, before/after, etc.)')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address from which the action was performed', null=True)),
                ('user_agent', models.TextField(blank=True, help_text='User agent of the client that performed the action')),
                ('severity', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')], default='info', help_text='Severity level of this action', max_length=20)),
                ('success', models.BooleanField(default=True, help_text='Whether the action completed successfully')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When this action occurred')),
                ('actor', models.ForeignKey(help_text='The account that performed this action', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs_as_actor', to='dockspace.mailaccount')),
            ],
            options={
                'verbose_name': 'Audit Log Entry',
                'verbose_name_plural': 'Audit Log Entries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-created_at'], name='dockspace_a_created_90f5fa_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['actor', '-created_at'], name='dockspace_a_actor_i_0bd3f8_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', '-created_at'], name='dockspace_a_action_a820a0_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['target_type', 'target_id'], name='dockspace_a_target__c3cbe7_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['severity', '-created_at'], name='dockspace_a_severit_e59b4d_idx'),
        ),
    ]
