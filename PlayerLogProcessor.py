from bs4 import BeautifulSoup
import re

def processor_log_file(input_dir, html_doc, output_dir):
    #output file
    #set-up output file for high level info including card supply
    high_level_output_file = html_doc[:-5] + '_summary.txt'
    
    #set-up output file for features - i.e. number of cards at the end of each round
    #TODO:
        
    #read and parse html
    file = open(input_dir + '/' + html_doc, mode = 'r')
    soup = BeautifulSoup(file, 'html.parser')
    
    #convert html contents into a list of tabs, navigable strings etc
    pre_tag = soup.find('pre')
    pre_tag.contents
    
    #first extract number of players and final score
    #look for entries of the form #n <name>: x points' - these are tagged with a 'b'
    players = []
    scores = []
    list_b_tags = soup.find_all('b');
    for tag in list_b_tags:
        s = tag.text
        if '#' in s:
            #extract name (assume string of form '#n ' comes before the name)
            players.append(s[3:])
            #next sibing contains the score, assume score is after a string of the form ': ' and is 2 digits long
            score_text = tag.next_sibling
            scores.append(score_text[2:4])
    
    #extract number of turns for this game
    total_turns = 0
    for (k,r) in enumerate(pre_tag.contents):
        if 'turn' in r.text:
            total_turns = int(re.search(r'\d+', r.text).group())
            break
    
    #following function parses a single line which consists of number of cards (unless equal to one) and card types
    #each separated by a colon and ended with a full stop or a horizontal dashed line. It returns a list of cards 
    #with card names duplicated according to the number of them in the row. Also the index of the full stop or 
    #dashed line will be returned
    def parse_row_into_cards(contents_list):
        card_list = []
        for (k,r) in enumerate(contents_list):
            #Need to be careful that the first content item doesn't contain a '....', causing 
            #the code to pickup a full stop
            if ((('.' not in r) or (k == 0)) and r.name == None and ('----------------------' not in r)):
                #check to see if trashing text contains the number of cards trashed
                #number is contained in last two digits of text
                try:
                    no_cards = int(r[-2:])
                except ValueError:
                    no_cards = 1
                #take next entry along which should be the card name
                card_type = r.next_sibling.text
                #and add copies of that to the dictionary
                for count in range(0,no_cards):
                    card_list.append(card_type)
            elif (('.' in r) or ('----------------------' in r)) and (k != 0):
                return (k, card_list)
    
    #next extract kingdom cards - first we deal with the case where the default set is chosen and players don't 
    #make changes
    
    #iterate through contents list under we find an element which contains 'cards in supply'. 
    default_supply_cards_start_index = 0
    for i, s in enumerate(pre_tag.contents):
        if 'cards in supply' in s:
            default_supply_cards_start_index = i
            break
    
    #there is an initial default set of supply cards. This may be modified later by player choice if this default 
    #selection is not chosen. So first determine if the players use the default set
    default_supply_set = False
    for s in pre_tag.contents[default_supply_cards_start_index:]:
        if 'Default card selection was used' in s:
            default_supply_set = True
            break
        elif '----------------------' in s:
            break
           
    #if the default set was used then grab card names
    supply_cards = [] 
    if default_supply_set == True:
        (index, cards) = parse_row_into_cards(pre_tag.contents[default_supply_cards_start_index:])
        supply_cards = cards
        
    #next we extract supply cards when players make a choice. In this case we look for the substring 'chosen cards are'
    #which tags the start of the set of chosen supply cards. This should be followed by a number of veto statements
    #dependent on the number of players
    index_end = 0 
    if default_supply_set == False:
        for (i,s) in enumerate(pre_tag.contents[default_supply_cards_start_index:]):
            if 'chosen cards are' in s:
                #loop over chosen supply cards
                (index, cards) = parse_row_into_cards(pre_tag.contents[default_supply_cards_start_index + i + 1:])
                index_end = default_supply_cards_start_index + i + index + 1
                supply_cards = cards
    
    #next each player can veto a card
    vetoed_cards = []
    for player in players:
        for s in pre_tag.contents[index_end:]:
            check_string = player + ' vetoes'
            if check_string in s:
                vetoed_cards.append(s.next_sibling.text)
    
    #remove vetoed cards from list of supply cards
    supply_cards = list(filter(lambda x: x not in vetoed_cards, supply_cards))
    
    #next loop through the turns and extract and bought or gained cards
    
    #use a dictionary of dictionaries to track gained cards by turn by player, and initialise keys
    incremental_cards_by_turn = {}
    for player in players:
        incremental_cards_by_turn[player] = {}
        for turn in range(1,total_turns+1):
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
            incremental_cards_by_turn[player][turn] = {}
        for turn in range(1,total_turns+1):
            incremental_cards_by_turn[player][turn]['buys'] = {}
            incremental_cards_by_turn[player][turn]['trashing'] = {}
            incremental_cards_by_turn[player][turn]['gaining'] = {}
            incremental_cards_by_turn[player][turn]['trashes'] = {}
        
    for player in players:
        turn_counter = 1
        #string to check for a buy action
        check_buy = player + ' buys'
        #string to check if current player is trashing a card
        check_trashing = 'trashing'
        #string to check if current player is gaining a card
        check_gaining = 'gaining'
        #string to check if another player trashes a card. Howver, current player can both 'trashes' 
        #and 'trashing'. Also it is possible for a player to trash nothing
        check_player_trashes = [x + ' trashes' for x in players] # need to check this!
        #string to check if another player is gains a card (gains is used rather than
        #gaining when a player gets a card out of turn)
        check_player_gains = [ x + ' gains' for x in players]
        #string to check end of turn
        check_turn_end = '(' + player + ' draws:'
        for (i,p) in enumerate(pre_tag.contents[index_end:]):
            check_turn = player + '\'s' + ' turn ' + str(turn_counter)
            if check_turn in p:
                buy_card_list = []
                trashing_card_list = []
                gaining_card_list = []
                gains_card_list = {} #needs to be a dictionary as multiple players may gain in another player's round
                trashes_card_list = {} #needs to be a dictionary as multiple players may need to trash in another player's round
                for (j,q) in enumerate(pre_tag.contents[index_end + i:]):
                    player_gains_list = [ x in q for x in check_player_gains]
                    player_trashes_list = [ x in q for x in check_player_trashes]
                    if check_buy in q:
                        (index, cards) = parse_row_into_cards(pre_tag.contents[index_end + i + j:])
                        buy_card_list = cards
                    elif check_trashing in q:
                        if 'trashing nothing' in r:
                            break
                        (index, cards) = parse_row_into_cards(pre_tag.contents[index_end + i + j:])
                        trashing_card_list = cards
                    elif check_gaining in q:
                        #also we need to check for a 'gaining nothing' case
                        if 'gaining nothing' in r:
                            break
                        else:
                            (index, cards) = parse_row_into_cards(pre_tag.contents[index_end + i + j:])
                            gaining_card_list = cards
                    elif any(player_gains_list):
                        #next we check if an opponent gains a card, e.g. a curse card
                        #need to loop through opponents
                        for (index, player_gains_check) in enumerate(player_gains_list):
                            if player_gains_check == True:
                                player_ = players[index]
                                (index_, cards) = parse_row_into_cards(pre_tag.contents[index_end + i + j:])
                                gains_card_list[player_] = cards
                    elif any(player_trashes_list):
                        #next we check if an opponent trashes a card
                        for (index, player_trashes_check) in enumerate(player_trashes_list):
                            if player_trashes_check == True:
                                player_ = players[index]
                                (index_, cards) = parse_row_into_cards(pre_tag.contents[index_end + i + j:])
                                trashes_card_list[player_] = cards
                    elif check_turn_end in q.text:
                        incremental_cards_by_turn[player][turn_counter]['buys'] = buy_card_list
                        incremental_cards_by_turn[player][turn_counter]['trashing'] = trashing_card_list
                        incremental_cards_by_turn[player][turn_counter]['gaining'] = gaining_card_list
                        for player_ in gains_card_list.keys():
                            incremental_cards_by_turn[player_][turn_counter]['gains'] = gains_card_list[player_] 
                        for player_ in trashes_card_list.keys():
                            incremental_cards_by_turn[player_][turn_counter]['trashes'] = trashes_card_list[player_] 
                        turn_counter += 1
                        break
         
    
    #first categorise supply cards if possible
    supply_sets= {}
    supply_sets['SizeDistortion'] = ['Artisan', 'Bandit', 'Bureaucrat', 'Chapel', 'Festival', 'Gardens', 'Sentry', 
                                        'Throne Room', 'Witch','Workshop']
    
    def check_known_supply_set(supply_sets_dict, cards):
        # Sort both lists
        for card_set in supply_sets_dict.keys():
            sorted_card_set = sorted(supply_sets_dict[card_set])
            sorted_cards = sorted(cards)
            # Compare the sorted lists
            if sorted_card_set == sorted_cards:
                return card_set
        return 'Unmatched'
        
    #first output high level information, including number of players, the set of supply cards and if the set of 
    #supply cards is recognised
    supply_set_match = check_known_supply_set(supply_sets, supply_cards)
    output_file = output_dir  + supply_set_match + '/' + high_level_output_file
    with open(output_file, 'w') as file:
        file.write('Input log: ' + html_doc + '\n')
        file.write('Number of Players: ' + str(len(players)) + '\n')
        file.write('Final Scores: ' + ','.join(scores)+ '\n')
        file.write('Supply cards: ' + ','.join(supply_cards)+ '\n')
        
    return None


