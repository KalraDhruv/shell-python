class ShellTokenizer:
    @staticmethod
    def tokenize(terminal_input):
        index = 0
        in_single_quotes = False
        in_double_quotes = False
        is_backslash = False
        is_space = False
        one_encountered_for_redirect = False
        tokens = []
        current_token = [] 
        for char in terminal_input:

            if is_backslash:
                current_token.append(char)
                is_backslash = False
                continue
            if char == "1" and not in_single_quotes and not in_double_quotes:
                one_encountered_for_redirect = True
                continue
            if (one_encountered_for_redirect and char == ">") or char == ">":
                one_encountered_for_redirect = False
                tokens.append(">")
                continue
            elif one_encountered_for_redirect and char != ">":
                one_encountered_for_redirect = False
                current_token.append("1")

            if char == "\\":
                if in_single_quotes:
                    current_token.append(char)
                else:
                    is_backslash = True
                continue
            if char == "\"" and not in_single_quotes:
                if not in_double_quotes:
                    in_double_quotes = True
                    continue
                elif in_double_quotes:
                    in_double_quotes = False
                    continue

            if char == "'" and not in_double_quotes:
                if not in_single_quotes:
                    in_single_quotes = True
                    continue
                elif in_single_quotes:
                    in_single_quotes = False
                    continue
            
                
            if char != " ":
                current_token.append(char)
                is_space = False
            elif in_double_quotes or in_single_quotes:
                current_token.append(char)
            else: 
                if is_space == False:
                    tokens.append("".join(current_token))
                    current_token = []
                is_space = True
                continue
        if len(current_token) > 0:
            tokens.append("".join(current_token))
        return tokens
