
# Import the necessary libraries
from PIL import Image
import pytesseract
import pyautogui
import keyboard
import pandas as pd
from difflib import SequenceMatcher
import time
from os import listdir
import numpy as np

# Function to use difflib's SequenceMatcher to compare strings
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Function to use pytesseract to convert image to text
def imgConvert(image):
    result = pytesseract.image_to_string(image, lang='eng')
    arr = result.split('\n')[0:-1]
    return arr

# Function that reduces and image only to it's darker pixels,
# removing as much bakcground noise as possible to increase the 
# reliability of pyTesseract
def reduceImage(image, intensity):
    image = np.array(image)
    height, width, channel = image.shape
    for x in range(width):
        for y in range(height):
            if np.sum(image[y][x]) > intensity:
                image[y][x] = np.array([255, 255, 255])

    image = Image.fromarray(image)
    return image

# Function that takes in text converted from images and removes noise
def arrClean(arr):
    newArr = []
    # removes blank elements and spaces from the input array
    for i in arr:
        if str.isspace(i):
            arr.remove(i)
        if i == '':
            arr.remove(i)
            
    # necessary to catch any escaped blanks unknown why the previos lines
    # do not catch these
    for i in arr:
        if i == '':
            arr.remove(i)
                
    # checks for exceptions in the Pokemon's name before removing noise
    if ' '.join(arr[0].split(" ", 2)[:2]) in SpaceNames:
        arr[0] = ' '.join(arr[0].split(" ", 2)[:2])
    elif 'Alola' in arr[0] or 'Galar' in arr[0]:
        arr[0] = arr[0].split(')', 1)[0] + ")"
    else:
        arr[0] = arr[0].split(' ', 1)[0]

    # if the Pokemon name is not correct finds the closest name in the
    # dataset and uses that instead
    correct = ''
    similarity = 0
    if arr[0] not in Names_list:
        print(arr[0], " has not been found")
        for i in Names_list:
            if similarity < similar(arr[0], i):
                    correct = i
                    similarity = similar(arr[0], i)
        arr[0] = correct 
        print("Closest Name: ", arr[0])
        
    # reverses the array to make it easier to deal with the moves which
    # are stored at the end of the array
    arr.reverse()
    
    # Checks if all the moves exist if not find and use the move with
    # the most similar name
    for i in range(4):
        correct = ''
        similarity = 0
        for j in Moves_list:
            if similarity < similar(arr[i], j):
                correct = j
                similarity = similar(arr[i], j)
        arr[i] = correct 
        
    # Puts the array back into the original order
    arr.reverse()
    ability_item = arr[2].split(" / ")
    stats = arr[3].split(" / ")
    newArr = arr[:2] + ability_item + stats + arr[4:]
    
    # final check for any empty strings
    while("" in newArr):
        newArr.remove("") 
      
    # returns the noiseless array
    return(newArr)

# Opens the needed data sets and converts to lists for easier use
Moves_df = pd.read_csv('All_Moves.csv', encoding = 'latin1')
Moves_list = Moves_df['Name'].tolist()
Pokemon_df = pd.read_csv('Pokemon.csv', encoding = 'latin1')
Names_list = Pokemon_df['Name'].tolist()

# Includes the tesseract executable in the path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Stores the screen locations of the four moves which are always
# in the same place 
movesPosition = [[259,622],[489,622],[259,691],[489,691]]        

# Lists of exceptions that need to considered
SpaceNames = ['Mr. Mime', 'Type: Null', 'Tapu Bulu', 'Tapu Koko', 'Tapu Lele', 'Tapu Fini', 'Mr. Rime']
EntryHazardMoves = [['Spikes',3],['Stealth Rock',1],['G-Max Stonesurge',1],['Toxic Spikes',2],['Sticky Web',1],['G-Max Steelsurge',1]]
HealMoves = ['Heal Order','Milk Drink','Moonlight','Morning Sun','Purify','Recover','Rest','Roost','Shore Up','Slack Off','Soft-Boiled','Strength Sap','Synthesis']

# Instantiates the array that keeps track of which Pokemon are still useable
Fainted = [False]*6

# The main gameplay loop
run = True
while run:
    # Empty lists used to store the position of various UI elements that
    # are calculated at the start of the battle
    mousePosition = []
    nameScreenshotPosition = []
    movesScreenshotPosition = []
    HealthScreenshotPosition = []
    StatsScreenshotPosition = []
    defaultStatsList = []

    
    # Binds the AI to a key so that it only starts when the user wants
    # it to, allowing any necessary preparation        
    if keyboard.read_key() == "#":
        # Sets initial variables
        Turn = 1
        StageHazards = []
        
        # Opens the Switch Menu to allow the AI to collect the
        # information it needs 
        pyautogui.moveTo(877, 728)
        pyautogui.click()
        
        # Locates the timer button on screen as the where the mouse needs
        # to be to find the information on team changes depending on where
        # this button is
        Pos = pyautogui.locateCenterOnScreen("TeamPokemonPoint.png", confidence = 0.9)
        FirstSlot = [Pos[0]-450,Pos[1]+40]
        # Calculates and appends all the needed positions to gather
        # information to various arrays
        for i in range(3):
            mousePosition.append([FirstSlot[0]+(i*150),FirstSlot[1]])
            nameScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-269])
            movesScreenshotPosition.append([FirstSlot[0]-68+(i*160),FirstSlot[1]-128])
            HealthScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-215])
            StatsScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-158])
        for i in range(3):
            mousePosition.append([FirstSlot[0]+(i*150),FirstSlot[1]+50])
            nameScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-269])
            movesScreenshotPosition.append([FirstSlot[0]-68+(i*160),FirstSlot[1]-128])
            HealthScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-215])
            StatsScreenshotPosition.append([FirstSlot[0]-85+(i*160),FirstSlot[1]-158])
            
        # Collects Team Data
        TeamList = []
        for i in range(6):
            # Finds and takes a screenshot of the Pokemon's name
            pyautogui.moveTo(mousePosition[i][0], mousePosition[i][1])
            image = pyautogui.screenshot(region = (nameScreenshotPosition[i][0],nameScreenshotPosition[i][1],300,23))
            
            # Makes image easier to convert
            image = reduceImage(image, 300)
            # Converts to screenshot to text            
            arr = imgConvert(image)
                 
            # Finds the moves each Pokemon has
            image = pyautogui.screenshot(region = (movesScreenshotPosition[i][0],movesScreenshotPosition[i][1],200,90))
            moveArr = imgConvert(image)
            # if all moves weren't found try again with less background noise
            if len(moveArr) < 4:
                image = reduceImage(image, 300)
                moveArr = imgConvert(image)
              
            arr += moveArr    
            pokemonArr = []
            pokemonArr = arrClean(arr)
            exportList = []
            slotList = []
            sortList = []
            
            # Creates two lists, one for the AI to use during decision
            # making, and one to export to the Move Probabilty data set
            slotList = pokemonArr[1:]
            for j in slotList:
                sortList.append(j)
            sortList.sort()
            slotList.insert(0, pokemonArr[0])
            sortList.insert(0, pokemonArr[0])     
            
            exportList.append(sortList)
            TeamList.append(slotList)
            
            # Collects the Pokemon's statistics in case the AI fails to
            # gather them properly at some point and needs something to 
            # fall back on
            image = pyautogui.screenshot(region = (StatsScreenshotPosition[i][0],StatsScreenshotPosition[i][1],440,23))
            stats = imgConvert(image)
            stats = stats[0]
            if "//" in stats:
                stats = stats.replace("//", "/")
            stats = stats.replace(" ", "")
            stats = stats.split("/")
            stat = []
            for i in stats:
                temp = []
                temp.append(i[:3])
                temp.append(i[3:])
                if temp[1][0] == " ":
                    temp[1] = temp[1][1:]
                stat.append(temp)
            defaultStatsList.append(stat)
           
            # exports the sorted list to the data set
            export = pd.DataFrame (exportList, columns = ['Name', 'Move 1', 'Move 2', 'Move 3' ,'Move 4'])
            export.to_csv('Move Probability.csv', index = False, header=None, mode='a')

        # Cleans up the Move Probability data set to make it easy to use
        MProb_df = pd.read_csv('Move Probability.csv')
        Prob_list = []
        for index, rows in MProb_df.iterrows():
            temp_list =[rows.Name, rows.move_1, rows.move_2, rows.move_3, rows.move_4]
            Prob_list.append(temp_list)
          
        # Removes repeat values and instead updates the times they've appeared
        uniqueList = []
        for i in Prob_list:
            append = True
            for j in uniqueList:
                if i == j:
                    append = False
            if append:
                uniqueList.append(i)
        
        for i in uniqueList:
            i.append(Prob_list.count(i))
           
        export = pd.DataFrame (uniqueList, columns = ['Name','move_1','move_2','move_3','move_4','amount'])
        export.to_csv('Move Probability.csv', index = False, header=True)
        
        # Prints out the team for testing and display purposes
        print("Current Team: \n")
        counter = 0
        for lst in TeamList:    
            print(lst[0])
            print(f"Moves: {lst[1]}, {lst[2]}, {lst[3]}, {lst[4]}")    
            print(f"Stats: {defaultStatsList[counter][0][0]}: {defaultStatsList[counter][0][1]}", end = ", ")
            print(f"{defaultStatsList[counter][1][0]}: {defaultStatsList[counter][1][1]}", end = ", ")
            print(f"{defaultStatsList[counter][2][0]}: {defaultStatsList[counter][2][1]}", end = ", ")
            print(f"{defaultStatsList[counter][3][0]}: {defaultStatsList[counter][3][1]}", end = ", ")
            print(f"{defaultStatsList[counter][4][0]}: {defaultStatsList[counter][4][1]}\n")
            counter += 1
            
        onField = 1
        # Battle Loop starts here
        while True:
            print(f'Turn {Turn}\n')

            # Opens the Pokemon Selection menu
            pyautogui.moveTo(877, 728)
            pyautogui.click()
        
            # Collects the current stats of all pokemon to take into
            # account any stat changes
            statsList = []
            for i in range(6):
                pyautogui.moveTo(mousePosition[i][0], mousePosition[i][1])
                
                image = pyautogui.screenshot(region = (HealthScreenshotPosition[i][0],HealthScreenshotPosition[i][1],300,23))
                health = imgConvert(image)

                try:
                    health = health[0]
                except:
                    health = ""
                    
                if 'fainted' in health:
                    Fainted[i] = True
                    
                image = pyautogui.screenshot(region = (StatsScreenshotPosition[i][0],StatsScreenshotPosition[i][1],440,23))
                stats = imgConvert(image)
                try:
                    stats = stats[0]
                    if "//" in stats:
                        stats = stats.replace("//", "/")
                    
                    stats = stats.split(" / ")
                    stat = []
                    for i in stats:
                        temp = []
                        temp.append(i[:3])
                        temp.append(i[4:])
                        stat.append(temp)
                except:
                    stat = defaultStatsList[i]
                
                statsList.append(stat)
            
            # Collects Opponent Name Data
            pyautogui.moveTo(643, 452)

            # Searches for the Opponents information
            width, height = pyautogui.size()
            imagePos = (width,0)
            for i in listdir("Type Finder"):
                try:
                    newPos = pyautogui.locateCenterOnScreen("Type Finder/" + i, confidence = 0.9)
                    if newPos[0] < imagePos[0]:
                        imagePos = newPos
                except:
                    pass
            
            image = pyautogui.screenshot(region = (imagePos[0]-25,imagePos[1]-32,300,23))
            
            Opp = imgConvert(image)
            
            # Checks for transformed Pokemon
            if "Type changed" in Opp[0]:
                Opp[0] = TeamList[0][0]
            
            if "Wishi" in Opp[0]:
                Opp[0] = "Wishiwashi"
            # Checks for exceptions to conventional naming
            if ' '.join(Opp[0].split(" ", 2)[:2]) in SpaceNames:
                Opp[0] = ' '.join(Opp[0].split(" ", 2)[:2])
            elif 'Alola' in Opp[0]:
                Opp[0] = Opp[0].split(')', 1)[0] + ")"
            else:
                Opp[0] = Opp[0].split(' ', 1)[0]
            
            # If the Opponent isn't found the first time try again
            # with background noise removed
            if Opp[0] not in Names_list:
                print(Opp[0], " has not been found")
                image = reduceImage(image, 200)
                Opp = imgConvert(image)
                
                if ' '.join(Opp[0].split(" ", 2)[:2]) in SpaceNames:
                    Opp[0] = ' '.join(Opp[0].split(" ", 2)[:2])
                elif 'Alola' in Opp[0]:
                    Opp[0] = Opp[0].split(')', 1)[0] + ")"
                else:
                    Opp[0] = Opp[0].split(' ', 1)[0]
                
            correct = ''
            similarity = 0
            if Opp[0] not in Names_list:
                print(arr[0], " has still not been found")
                for i in Names_list:
                    if similarity < similar(arr[0], i):
                            correct = i
                            similarity = similar(arr[0], i)
                Opp[0] = correct 
                print("Closest Name: ", arr[0])
                
            Opp = Opp[0]
                
            print("Opponent: " + Opp + "\n")
            
            # Calculates the probabilty of move types
            Opp_moves_df = pd.read_csv('Move Probability.csv')
            Opp_moves_df = Opp_moves_df[Opp_moves_df['Name'] == Opp]
            Opp_moves = Opp_moves_df.values.tolist()
            
            #Calculates Viability
            eff_df = pd.read_csv('Pokemon.csv')
            rslt_df = eff_df[eff_df['Name'] == Opp]
            pointList = []
            counter = 0
            for lst in TeamList:
                # Calculates the weoght of each of the opponents moves
                TotalMoves = []
                UniqueMoves = []
                MoveAmount = []
                weight = 0
                weakness = eff_df[eff_df['Name'] == lst[0]]
                for i in Opp_moves:
                    for j in range(1,5):
                        MoveInfo_df = Moves_df[Moves_df['Name'] == i[j]]
                        MoveInfo = MoveInfo_df.values.tolist()
                        MoveInfo = MoveInfo[0]
                        if MoveInfo[3] == '-':
                            MoveInfo[3] = 1
                        if MoveInfo[4] == '-':
                            MoveInfo[4] = 1
                        MoveDamage = float(MoveInfo[3])*float(MoveInfo[4])*(weakness[MoveInfo[1]].values.tolist())[0]
                        TotalMoves.append([MoveInfo[0],MoveDamage])
                        
                for i in TotalMoves:
                    if i not in UniqueMoves:
                        UniqueMoves.append(i)
                for i in UniqueMoves:
                    total = (TotalMoves.count(i))/len(TotalMoves)
                    MoveAmount.append(total)
                
                for i in range(0,len(UniqueMoves)):
                    weight += UniqueMoves[i][1]*round(MoveAmount[i], 2)

                # Calculates the value of each move to decide what to do
                points = []
                PokeStats = statsList[counter]
                currentPokemon = pd.read_csv('Pokemon.csv')  
                currentPokemon = currentPokemon[currentPokemon['Name'] == lst[0]]
                currentPokemon = currentPokemon.values.tolist()
                # Checks if it has the right stats
                if len(PokeStats) != 5:
                    PokeStats = defaultStatsList[counter]
                for i in range (1,5):
                    STAB = 1
                    Mv_df = Moves_df[Moves_df['Name'] == lst[i]]
                    move = Mv_df.values.tolist()
                    moveType = move[0][1]
                    moveStat = move[0][2]
                    moveDamage = move[0][3]
                    moveAccuracy = move[0][4]
                    
                    if moveDamage == '-':
                        moveDamage = 1
                    
                    # Considers using stat moves based on how long that
                    # Pokemon has been on the field for
                    if moveStat == 'Status' and move[0][0] not in HealMoves:
                        if counter == 0:
                            moveDamage = 100/onField
                        else:
                            moveDamage = 40
                            
                    # Considers using Entry Hazards if the max amount of
                    # that hazard isnt on stage yet
                    for i in EntryHazardMoves:
                        if i[0] == move[0][0] and i[1] != 0:
                            moveDamage = 120
                            i[1] -= 1
                            
                    # Checks if the current pokemon needs healing
                    if pyautogui.pixel(212,453) != (0, 187, 81) and move[0][0] in HealMoves:
                                moveDamage = 100
                       
                    # Considers the stat that governs the strength of the
                    # move
                    atkStat = 0
                    if moveStat == 'Physical':
                        atkStat = PokeStats[0][1]
                    if moveStat == 'Special':
                        atkStat = PokeStats[2][1]
                    if moveStat == 'Status':
                        atkStat = PokeStats[4][1]
                        
                    if moveAccuracy == '-':
                        moveAccuracy = 1
                        
                    if moveType == currentPokemon[0][2] or moveType == currentPokemon[0][3]:
                        STAB = 1.5
                        
                    try:
                        Speed = float(PokeStats[4][1])
                    except:
                        Speed = float(defaultStatsList[counter][4][1])
                    
                    # Calculates total value of each move
                   
                    totalpoints = float(((rslt_df[moveType]*float(moveDamage)*STAB))-weight)*float(atkStat)*float(moveAccuracy)*Speed
                    
                    # if that pokemon is not already on the field halve 
                    # the value to simulate a turn being lost switching
                    # that pokemon in
                    if counter != 0:
                        totalpoints = totalpoints/2
                    
                    # Sets negative values to 1 to make even a extremely poor
                    # choice better than trying to use a Pokemon that is no
                    # longer useable
                    if totalpoints<=0:
                        totalpoints = 1
                    
                    # If a Pokemon is no longer useable set all it's value to
                    # zero so the AI doesn't try to use them
                    if Fainted[counter] == True:
                        totalpoints = totalpoints*0
                        
                    points.append(totalpoints)
                pointList.append(points)
                
                counter += 1
             
            # Prints the probability of an Opponent having a move
            print("Moves: ", end="")
            for i in range(0,len(UniqueMoves)):
                print(f"{UniqueMoves[i][0]} - {round(MoveAmount[i]*100, 2)}%", end = "   ")
            print("")   
                
            # Prints the value of each decision
            for i in range (0,6):
                print(TeamList[i][0])
                print(TeamList[i][1] + ": " + str(pointList[i][0]))
                print(TeamList[i][2] + ": " + str(pointList[i][1]))
                print(TeamList[i][3] + ": " + str(pointList[i][2]))
                print(TeamList[i][4] + ": " + str(pointList[i][3]))
                print("Best: " + str(max(pointList[i])) + '\n')
                
            # Finds the order of best choices in case something happens
            # that makes the first choice no longer useable
            maxList = []
            for i in pointList:
                maxList.append(max(i))
            swap = maxList.index(max(maxList))
            faintSwap = maxList.index(sorted(maxList, reverse=True)[1])
            
            # if the best choice doesnt require swapping in
            if swap == 0:
                # increases how long the Pokemon has been on the field for
                onField += 1
                counter = 1
                # Opens the Attack menu
                pyautogui.moveTo(86, 726)
                pyautogui.click()
                # Picks the best option
                index = pointList[swap].index(max(pointList[swap]))
                pyautogui.moveTo(movesPosition[index][0], movesPosition[index][1])
                pyautogui.click()
                time.sleep(2)
                # if that option is not available pick the next best option
                # until an option is available
                attacking = (0,0)
                while attacking != None:
                    attacking = pyautogui.locateCenterOnScreen("CheckAttack.png")
                    if attacking != None:
                        index = pointList.index(sorted(pointList, reverse=True)[counter])
                        pyautogui.moveTo(movesPosition[index][0], movesPosition[index][1])
                        pyautogui.click()
                        pyautogui.moveTo(attacking[0]+50,attacking[1])
                    counter += 1
                    
            # if the best move is to swap out
            else:
                onField = 1
                counter = 1
                attemptSwap = True
                while attemptSwap:
                    pyautogui.moveTo(mousePosition[swap][0], mousePosition[swap][1])
                    pyautogui.click()
                    
                    # if the pokemon can not be swapped out take the best
                    # option with the pokemon already on field
                    trapped = pyautogui.locateCenterOnScreen("Trapped.png", confidence = 0.9)
                    if trapped != None:
                        pyautogui.moveTo(86, 726)
                        pyautogui.click()
                        pyautogui.moveTo(movesPosition[index][0], movesPosition[index][1])
                        pyautogui.click()
                        
                        attacking = (0,0)
                        while attacking != None:
                            attacking = pyautogui.locateCenterOnScreen("CheckAttack.png")
                            if attacking != None:
                                index = maxList.index(sorted(maxList, reverse=True)[counter])
                                pyautogui.moveTo(movesPosition[index][0], movesPosition[index][1])
                                pyautogui.click()
                                pyautogui.moveTo(attacking[0]+50,attacking[1])
                            counter += 1
                    # check if the Pokemon has fainted and the AI is unaware        
                    fainted = pyautogui.locateCenterOnScreen("FaintCheck.png", confidence = 0.5)
                    if fainted == None: 
                        attemptSwap = False
                    else:
                        Fainted[swap] = True
                        swap = maxList.index(sorted(maxList, reverse=True)[counter])
                    counter += 1
            
                TeamList[0], TeamList[swap] = TeamList[swap], TeamList[0]
                Fainted[0], Fainted[swap] = Fainted[swap], Fainted[0]
             
            # Checks if the next turn has started
            counter = 2    
            attacking = pyautogui.locateCenterOnScreen("CheckAttack.png", confidence = 0.9)
            while attacking == None:
                # sends out the second best pokemon in case of faint
                pyautogui.moveTo(mousePosition[0][0], mousePosition[0][1])
                pyautogui.click()
                fainted = pyautogui.locateCenterOnScreen("FaintCheck.png", confidence = 0.75)
                if fainted != None: 
                    pyautogui.click()
                    pyautogui.moveTo(mousePosition[faintSwap][0], mousePosition[faintSwap][1])
                    pyautogui.click()
                    Fainted[faintSwap] = True
                    TeamList[0], TeamList[faintSwap] = TeamList[faintSwap], TeamList[0]
                    faintSwap = maxList.index(sorted(maxList, reverse=True)[counter])
                    counter += 1
                attacking = pyautogui.locateCenterOnScreen("CheckAttack.png", confidence = 0.75)
                time.sleep(3)
                
            Turn += 1