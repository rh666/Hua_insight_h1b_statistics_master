import sys as sys
from Listsource import *

def isCertified(line, CaseStatusIndex):
    """
    :param line:
    :param CaseStatusIndex:
    :return: whether the case in current line is certified
    """
    return line.strip('\n').split(';')[CaseStatusIndex] == 'CERTIFIED'

def getIndex(firstline, indexName):
    """

    :param firstline: title line of the file
    :param indexName: like WorkStates SOCcode etc
    :return: the index number corresponding to the indexName
    """

    theName = 'notFound'

    for name in eval('nameList_' + indexName):
        if name in firstline.split(';'):
            theName = name
    if theName == 'notFound':
        print 'File structure has never been seen, nameList_' + indexName + ' need to be updated'
        return
    else:
        return firstline.split(';').index(theName)


def getValue(line, index):
    """

    :param line: currentline
    :param index: indexnumber
    :return: get the value under the index of the current line
    """
    return line.strip('\n').split(';')[index]


def getCleanSOCcode(SOCcode):
    """
    :param SOCcode: row code
    :return: cleaned SOC code
    """
    numSOCcode = ''.join(SOCcode.split('-')).strip()
    CleanSOCcode = numSOCcode[:2] + '-' + numSOCcode[2:6]
    return CleanSOCcode


def isNotSOCcode(SOCcode):
    """
    :param SOCcode: cleaned SOC code
    :return: determine if the SOC code is not the correct one. if the first 2 character of the input are not numerical numbers and
             and the total length of the input does not equals to 7 return True
    """
    curSOCcode = getCleanSOCcode(SOCcode)
    if (len(curSOCcode) != 7) | (not curSOCcode[:2].isdigit()):
        return True
    else:
        return False


def getSOCcode(line, SOCcodeIndex, nElements):
    """

    :param line: current line
    :param SOCcodeIndex: index number of SOC code column
    :param nElements: total elements in title
    :return: real SOC code. the real SOC code can be mis-aligned with the index number, check the next two rows
             to determine if the code is mis-aligned and return the correct code
    """
    SOCcode = getValue(line, SOCcodeIndex)
    curSOCcode = getCleanSOCcode(SOCcode)
    nCheckfollowinglines = 2
    for i in range(nCheckfollowinglines):
        if ((len(curSOCcode) != 7) | (not curSOCcode[:2].isdigit())) & (nElements - SOCcodeIndex - i > 1):
            SOCcode = getValue(line, SOCcodeIndex + i + 1)
            curSOCcode = getCleanSOCcode(SOCcode)
        else:
            return curSOCcode

    return curSOCcode


def getWorkState(line, WorkStateIndex, nElements):
    """

    :param line: current line
    :param WorkStateIndex: index number of work state
    :param nElements: total elements in the title
    :return: real work state . the real work state  can be mis-aligned with the index number, check the next two rows
             if not reach the end to determine if the work state is mis-aligned and return the correct code

    """

    WorkState = getValue(line, WorkStateIndex)
    nCheckfollowinglines = 2
    for i in range(nCheckfollowinglines):
        if (nElements - WorkStateIndex - i <= 1) or (WorkState in states):
            return WorkState
        else:
            WorkState = getValue(line, WorkStateIndex + i + 1)

    return WorkState


def updateDict(Key, Dict):
    """
    :param Key:
    :param Dict:
    :return: if key is in the dict add the values up, if not, add the key to the dict
    """
    if Key in Dict:
        Dict[Key] += 1
    else:
        Dict[Key] = 1


def getStatistics(Statedict, SOCcodedict, CodeToName, filename):
    """
    :param Statedict: dict to record the state and the number of certified applications
    :param SOCcodedict: dict to record the SOCcode and the number of certified applications
    :param CodeToName: dict from soccode to soc name
    :param filename: file to read
    :return: updated Statedict SOCcodedict and CodetoName dict
    """
    nLine = 0 # record total line number
    Ncertified = 0 # record total certified applications
    with open(filename, 'r') as f:
        for line in f:

            nLine += 1
            if nLine == 1:
                firstline = line.strip('\n')
                nElements = len(firstline.split(';'))
                WorkStateIndex = getIndex(firstline, 'WorkState')
                SOCcodeIndex = getIndex(firstline, 'SOCcode')
                SOCnameIndex = getIndex(firstline, 'SOCname')
                CaseStatusIndex = getIndex(firstline, 'CaseStatus')
                # get index number of the elements that we are interested in, namely Workstate, SOCcode and etc

            else:
                if isCertified(line, CaseStatusIndex):
                    # only consider the certified cases
                    Ncertified += 1

                    WorkState = getWorkState(line, WorkStateIndex, nElements) # get the correct WorkState for each certified application
                    updateDict(WorkState, Statedict) # then update the State dict

                    SOCcode = getSOCcode(line, SOCcodeIndex, nElements) # get the correct SOC code for each certified application
                    updateDict(SOCcode, SOCcodedict) # then update the SOC code dict

                    if getValue(line, SOCcodeIndex) not in CodeToName:
                        CodeToName[getValue(line, SOCcodeIndex)] = getValue(line, SOCnameIndex).strip('"')
                    # update the Code to name dict. This will be used to transfer SOC code back to name later

        return Statedict, SOCcodedict, CodeToName

def trasformCodetoName(SOCcodedict,SOCnamedict,CodeToName):
    """
    :return: update the SOCname dict using SOCcode dict and CodetoName dict
    """
    for key in SOCcodedict:
        try:
            SOCnamedict[CodeToName[key]] = SOCcodedict[key]
        except:
            continue


def getTop10percentage(Dict):
    """

    :param Dict: State dict or SOC name dict
    :return: top 10 by value in the dict including key, value, and percentage (value/total)
    """
    top10KeyValue = sorted(Dict.items(), key=lambda x: (-1 * x[1], x[0]))
    # sort dict by value in descending order and then by key in ascending oder in case of a tie breaker
    totalCertified = sum(Dict.values())
    # sum up the values in the dict

    top10 = []
    for i in range(min(10, len(top10KeyValue))):
        # top 10 values or all values if elements is less than 10
        percentage = float(top10KeyValue[i][1]) / float(totalCertified)
        # get the percentage
        percentage = '{percent:.1%}'.format(percent=round(percentage, 3))
        # format the percentage to one digit after decimal
        top10.append([top10KeyValue[i][0], str(top10KeyValue[i][1]), percentage])
        # save top10 information into a list

    return top10


def writeTofile(filename, top10List,indicator):
    """

    :param filename: file to write output
    :param top10List:
    :param indicator: indicate what is to be write out
    :return:
    """
    with open(filename, 'a+') as f:
        if indicator == 'occupation':
            f.write(';'.join(['TOP_OCCUPATIONS', 'NUMBER_CERTIFIED_APPLICATIONS', 'PERCENTAGE']) + '\n')
        elif indicator == 'state':
            f.write(';'.join(['TOP_STATES', 'NUMBER_CERTIFIED_APPLICATIONS', 'PERCENTAGE']) + '\n')
        for i in range(len(top10List)):
            f.write(';'.join(top10List[i]) + '\n')


def main():
    """

    :return:
    """
    Statedict = {}
    SOCcodedict = {}
    SOCnamedict = {}
    CodeToName = {}
    # initialize all the dict

    Statedict, SOCcodedict, CodeToName = getStatistics(Statedict, SOCcodedict, CodeToName, sys.argv[1])
    # update the dict

    trasformCodetoName(SOCcodedict, SOCnamedict, CodeToName)
    # update SOCname dict using SOCcode dict and CodeToName dict

    stateTop10 = getTop10percentage(Statedict)
    # get top 10 state information
    SOCnameTop10 = getTop10percentage(SOCnamedict)
    # get top 10 occupation information

    writeTofile(sys.argv[2], SOCnameTop10,'occupation') # write top 10 occupation out
    writeTofile(sys.argv[3],stateTop10,'state') # write top 10 state out



if __name__ == '__main__':
    main()
