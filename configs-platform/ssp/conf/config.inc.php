<?php
#==============================================================================
# LTB Self Service Password
#
# Copyright (C) 2009 Clement OUDOT
# Copyright (C) 2009 LTB-project.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# GPL License: http://www.gnu.org/licenses/gpl.txt
#
#==============================================================================

#==============================================================================
# Configuration
#==============================================================================
# LDAP
$ldap_url = "ldap://localhost";
$ldap_starttls = false;
$ldap_binddn = "cn=admin,dc=risoe,dc=dk"; #cn=manager,dc=example,dc=com";
$ldap_bindpw = "pw"; #"secret";
$ldap_base = "dc=risoe,dc=dk";
$ldap_login_attribute = "uid";
$ldap_fullname_attribute = "cn";
$ldap_filter = "(&(objectClass=person)($ldap_login_attribute={login}))";

# Active Directory mode
# true: use unicodePwd as password field
# false: LDAPv3 standard behavior
$ad_mode = false;
# Force account unlock when password is changed
$ad_options['force_unlock'] = false;
# Force user change password at next login
$ad_options['force_pwd_change'] = false;
# Allow user with expired password to change password
$ad_options['change_expired_password'] = false;

# Samba mode
# true: update sambaNTpassword and sambaPwdLastSet attributes too
# false: just update the password
$samba_mode = false;
# Set password min/max age in Samba attributes
#$samba_options['min_age'] = 5;
#$samba_options['max_age'] = 45;

# Shadow options - require shadowAccount objectClass
# Update shadowLastChange
$shadow_options['update_shadowLastChange'] = false;

# Hash mechanism for password:
# SSHA
# SHA
# SMD5
# MD5
# CRYPT
# clear (the default)
# auto (will check the hash of current password)
# This option is not used with ad_mode = true
$hash = "clear";

# Prefix to use for salt with CRYPT
$hash_options['crypt_salt_prefix'] = "$6$";

# Local password policy
# This is applied before directory password policy
# Minimal length
$pwd_min_length = 0;
# Maximal length
$pwd_max_length = 0;
# Minimal lower characters
$pwd_min_lower = 0;
# Minimal upper characters
$pwd_min_upper = 0;
# Minimal digit characters
$pwd_min_digit = 0;
# Minimal special characters
$pwd_min_special = 0;
# Definition of special characters
$pwd_special_chars = "^a-zA-Z0-9";
# Forbidden characters
#$pwd_forbidden_chars = "@%";
# Don't reuse the same password as currently
$pwd_no_reuse = true;
# Complexity: number of different class of character required
$pwd_complexity = 0;
# Show policy constraints message:
# always
# never
# onerror
$pwd_show_policy = "never";
# Position of password policy constraints message:
# above - the form
# below - the form
$pwd_show_policy_pos = "above";

# Who changes the password?
# Also applicable for question/answer save
# user: the user itself
# manager: the above binddn
$who_change_password = "manager";

## Questions/answers
# Use questions/answers?
# true (default)
# false
$use_questions = false;

# Answer attribute should be hidden to users!
$answer_objectClass = "extensibleObject";
$answer_attribute = "info";

# Extra questions (built-in questions are in lang/$lang.inc.php)
#$messages['questions']['ice'] = "What is your favorite ice cream flavor?";

## Token
# Use tokens?
# true (default)
# false
$use_tokens = true;
# Crypt tokens?
# true (default)
# false
$crypt_tokens = true;
# Token lifetime in seconds
$token_lifetime = "3600";

## Mail
# LDAP mail attribute
$mail_attribute = "mail";
# Who the email should come from
$mail_from = "admin@e-neutrons.org";
# Notify users anytime their password is changed
$notify_on_change = false;

## SMS
# Use sms
$use_sms = false;
# GSM number attribute
$sms_attribute = "mobile";
# Partially hide number
$sms_partially_hide_number = true;
# Send SMS mail to address
$smsmailto = "{sms_attribute}@service.provider.com";
# Subject when sending email to SMTP to SMS provider
$smsmail_subject = "Provider code";
# Message
$sms_message = "{smsresetmessage} {smstoken}";

# SMS token length
$sms_token_length = 6;

# Display help messages
$show_help = true;

# Language
$lang ="en";

# Logo
$logo = "style/e-neutrons-logo-blue-small.png"; #ltb-logo.png";

# Debug mode
$debug = false;

# Encryption, decryption keyphrase
$keyphrase = "secret";

# Where to log password resets - Make sure apache has write permission
# By default, they are logged in Apache log
#$reset_request_log = "/var/log/self-service-password";

# Invalid characters in login
# Set at least "*()&|" to prevent LDAP injection
# If empty, only alphanumeric characters are accepted
$login_forbidden_chars = "*()&|";

## CAPTCHA
# Use Google reCAPTCHA (http://www.google.com/recaptcha)
# Go on the site to get public and private key
$use_recaptcha = true;
$recaptcha_publickey = "6LchGBUTAAAAAIMqKpBHZ4qWEGBdKxPT9rFd5yZW";
$recaptcha_privatekey = "6LchGBUTAAAAAJJiOg5jCua0bGDBxPZ93BR9lHTk";
# Customize theme (see http://code.google.com/intl/de-DE/apis/recaptcha/docs/customization.html)
# Examples: red, white, blackglass, clean
$recaptcha_theme = "white";
# Force HTTPS for recaptcha HTML code
$recaptcha_ssl = false;

## Default action
# change
# sendtoken
# sendsms
$default_action = "sendtoken";

## Extra messages
# They can also be defined in lang/ files
#$messages['passwordchangedextramessage'] = NULL;
#$messages['changehelpextramessage'] = NULL;

# Launch a posthook script after successful password change
#$posthook = "/usr/share/self-service-password/posthook.sh";

?>
