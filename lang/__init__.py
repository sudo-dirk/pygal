#!/usr/bin/env python
# -*- coding: utf-8 -*-
from helpers import decode

LANGUAGE = 'DE'


if LANGUAGE == 'DE':
    admin = 'Administration'
    email_desc = 'Ihre E-Mail - Adresse'
    delete = decode('Löschen von %s')
    error_passwords_not_equal_userprofile = decode('Die eingegebenen Passwörter stimmen nicht überein! Das Passwort wurde nicht geändert.')
    error_passwords_not_equal_register = decode('Die eingegebenen Passwörter stimmen nicht überein! Der Benutzer wurde nicht angelegt.')
    error_password_empty_userprofile = decode('Das neue Passwort ist leer. Das Passwort wurde nicht geändet.')
    error_password_wrong_userprofile = decode('Das eingegebene Passwort stimmt nicht. Das Passwort wurde nicht geändert')
    error_password_wrong_login = decode('Die eingegebenen Zugangsdaten stimmt nicht. Login wurde nicht durchgeführt.')
    error_permission_denied = decode('Der Zugriff wurde verweigert. Bitte kontaktieren Sie den Administrator!')
    error_user_already_exists = decode('Der Benutzer existiert bereits! Der Benutzer wurde nicht angelegt. <a href="%s">Passwort vergessen?</a>')
    error_user_already_in_admin_group = decode('Der gewählte Benutzer ist bereits in der Administrator Gruppe. Bitte kontaktieren Sie den Administrator!')
    info_empty_search = decode('Die Suche hat keine Treffer ergeben.')
    info_item_deleted = decode('Das Element %s wurde erfolgreich entfernt.')
    info_login = decode('Wenn Sie keinen Account haben, <a href="%s">können Sie einen anlegen</a>. <a href="%s">Passwort vergessen?</a>')
    info_logout_performed = decode('Logout durchgeführt. Sie koennen sich <a href="%s">hier</a> anmelden.')
    info_lostpass = decode('Es reicht eins der beiden Felder auszufüllen.')
    info_tag_added = decode('Ein Tag mit dem Text "%s" wurde hinzu gefügt')
    info_tag_deleted = decode('Der Tag mit dem Text "%s" wurde entfernt')
    invalid_user = 'Ungueltiger Benutzer'
    login = 'Anmelden'
    login_desc = 'Der "Login" - Name'
    logout = 'Abmelden'
    lostpass = 'Zugangsdaten vergessen'
    password_desc = 'Das "Login" - Passwort'
    password2_desc = 'Passwort Wiederholung'
    permission_denied = 'Zugriff verweigert!'
    public_rights = decode('Rechte ohne Anmeldung setzen')
    register = 'Benutzerregistrierung'
    search = 'Suche'
    search_results = 'Sucheergebnisse: %s'
    title_info = 'Allgemeine Information'
    upload = 'Upload'
    user = decode('Benutzer')
    userprofile = 'Benutzerprofil editieren...'
    user_in_admin_group = "Der Benutzer %s ist bereits in der Administrator Gruppe registriert. Zum Anlegen des Benutzerprofils kontaktieren Sie bitte einen Administrator."
else:
    admin = 'Admin'
    email_desc = 'Your E-Mail adress'
    delete = decode('Delete of %s')
    error_passwords_not_equal_userprofile = 'The commited passwords are not equal! Password has not been changed.'
    error_passwords_not_equal_register = 'The commited passwords are not equal! Account has not been created.'
    error_password_empty_userprofile = 'The commited password is empty! Password has not been changed.'
    error_password_wrong_userprofile = 'Wrong password commited. Password has not been changed.'
    error_password_wrong_login = 'Wrong password commited. Login was not successfull.'
    error_permission_denied = 'Permission denied. Please contact the administrator.'
    error_user_already_exists = 'User already exists. Account has not been created. <a href="%s">Forgot your password?</a>'
    error_user_already_in_admin_group = 'This user is already in the admin group. Please contact the administrator.'
    info_empty_search = decode('No search results.')
    info_item_deleted = decode('Item %s had been successfully deleted.')
    info_login = 'If you do not have an account, <a href="%s">you can create one now</a>. <a href="%s">Forgot your password?</a>'
    info_logout_performed = 'Logout performed. You are able to login<a href="%s">here</a>.'
    info_lostpass = 'Please note that you only need to fill out one form field.'
    info_tag_added = 'A tag named "%s" has been added'
    info_tag_deleted = decode('The tag named "%s" has been deleted')
    invalid_user = 'Invalid User'
    login = 'Login'
    login_desc = 'The login name'
    logout = 'Logout'
    lostpass = 'Account data forgotten'
    password_desc = 'The login password'
    password2_desc = 'Repeat the same password'
    permission_denied = 'Permission denied!'
    public_rights = decode('Set public rights')
    register = 'Register'
    search = 'search'
    search_results = 'Search results: %s'
    title_info = 'Information'
    upload = 'Upload'
    user = 'User'
    userprofile = 'Edit Userprofile...'
    user_in_admin_group = "Unable to create user %s. User is already part of the Admin-Group. Please contact the Administrator of this page."
