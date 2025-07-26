from password_validator import PasswordValidator

min_max_length_schema = PasswordValidator()
upper_and_lower_schema = PasswordValidator()
digit_no_spaces_schema = PasswordValidator()
symbol_schema = PasswordValidator()

min_max_length_schema\
.min(15)\
.max(40)\

upper_and_lower_schema\
.has().uppercase()\
.has().lowercase()

digit_no_spaces_schema\
.has().digits()\
.has().no().spaces()

symbol_schema\
.has().symbols()