import collections

# # список можно оставить здесь или передавать как аргумент
# SPECIAL_CASES = [
#     'Paris', 'Warrens', 'Luxembourg', 'Epinay', 'Geneva', 'Theresa', 
#     'France', 'Diderot', 'Grimm', 'Abbe', 'Houdetot', 'Hermitage', 'French', 
#     'Mademoiselle', 'Dupin', 'Madam de Warrens','Madam de Dupin'
# ]

def capitalization(index, text_list, special_cases_list):
    if index < 0 or index >= len(text_list):
        return False

    ch = text_list[index]
    if not ch.isalpha():
        return False

    # П1: Первая буква в тексте
    if index == 0:
        return True

    if index >= 2 and text_list[index - 1].isupper() and text_list[index - 2].isupper():
        return False

    # П* правило для специальных слов
    for special_phrase in special_cases_list:
        if len(special_phrase) > index + 1: continue
        for phrase_char_idx in range(len(special_phrase)):
            text_start_idx_for_match = index - phrase_char_idx
            if text_start_idx_for_match >= 0 and \
               text_start_idx_for_match + len(special_phrase) <= len(text_list):
                segment_in_text = "".join(text_list[text_start_idx_for_match : text_start_idx_for_match + len(special_phrase)])
                if segment_in_text.lower() == special_phrase.lower():
                    return special_phrase[phrase_char_idx].isupper()

    # П2: После .!?
    if index > 0:
        j = index - 1
        saw_space_or_newline = False
        while j >= 0 and text_list[j].isspace():
            saw_space_or_newline = True
            j -= 1
        if saw_space_or_newline and j >= 0 and text_list[j] in '.!?':
            return True

    # П4: Изолированное 'I'
    if ch.lower() == 'i':
        prev = text_list[index - 1] if index > 0 else ' '
        next_ch = text_list[index + 1] if index + 1 < len(text_list) else ' '
        
        if not prev.isalpha() and not next_ch.isalpha():
            if next_ch == '.':
                next_next_ch = text_list[index + 2] if index + 2 < len(text_list) else ' '
                if next_next_ch.isalpha():
                    return False 
            return True
            
    return False

def find_word_at_index(text_content, index):
    if not text_content[index].isalpha():
        return ""
    start = index
    while start > 0 and text_content[start - 1].isalpha():
        start -= 1
    end = index
    while end < len(text_content) - 1 and text_content[end + 1].isalpha():
        end += 1
    return text_content[start : end + 1]

def exeption_counter(text, SPECIAL_CASES):  
    words_with_mismatches_counts = collections.Counter()
    mismatches_count = 0  
    exception_markers = [0] * len(text)
    for i, original_char in enumerate(text):
        if original_char.isalpha():
            should_be_capital = capitalization(i, text, SPECIAL_CASES)
            is_capital_original = original_char.isupper()

            if should_be_capital != is_capital_original:
                exception_markers[i] = 1 # исключение
                mismatches_count += 1
                word = find_word_at_index(text, i)
                if word:
                    words_with_mismatches_counts[word] += 1
    return exception_markers

def decapitalize_text(text, special_cases):
    #  функция принимает текст,  не имя файла
    text_lower = text.lower()
    exception_list = exeption_counter(text, special_cases)
    return text_lower, exception_list

def exeptions_dist(exception_markers):    
    distances = []
    last_one_index = -1
    for i, marker in enumerate(exception_markers):
        if marker == 1:
            if last_one_index == -1: # Первая единица
                distances.append(i)
            else:
                distances.append(i - last_one_index)
            last_one_index = i
    return distances

def recapitalize(distance_list, decapitalized_text, special_cases_list):
    # восстановить  индексы искл
    exception_indices = set()
    current_index = 0
    if distance_list:
        current_index = distance_list[0]
        exception_indices.add(current_index)
        for i in range(1, len(distance_list)):
            current_index += distance_list[i]
            exception_indices.add(current_index)


    result_chars = list(decapitalized_text)


    for i, char in enumerate(result_chars):
        if not char.isalpha():
            continue

        rule_says_upper = capitalization(i, result_chars, special_cases_list)
        
        is_an_exception = i in exception_indices
        
        # XOR
        if rule_says_upper ^ is_an_exception:
            result_chars[i] = char.upper()
        else:
          
            result_chars[i] = char.lower()
            
    return "".join(result_chars)
