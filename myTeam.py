# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveAgentZ', second = 'DefensiveAgentZ'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class AgentZero(CaptureAgent):

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    # Find base border
    xStart = self.start[0]
    if xStart == 1: self.basePos = (15.0, 7.0)
    else: self.basePos = (16.0, 8.0)
    CaptureAgent.registerInitialState(self, gameState)

  # Picks among the actions with the highest Q(s, a)
  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)

    # Calculate evaluation time per move by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print('eval time for agent %d: %.4f' % (self.index, time.time() - start))

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    foodLeft = len(self.getFood(gameState).asList())

    # print('~~~~~~ Begin ~~~~~')
    # print('Best Actions:', bestActions)
    # print('~~~~~~ End ~~~~~~~')

    # time.sleep(1)

    if foodLeft == 0:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start, pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  # Finds next successor which is a grid position (location tuple)
  def getSuccessor(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      return successor.generateSuccessor
    else:
      return successor
  
  # Computes a linear combination of features and weights
  def evaluate(self, gameState, action):
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    # print('Action:', action)
    # # print('GameState:', gameState, sep='\n')
    # print('Features:', features)
    # print('Weights:', weights)
    # print('~ features * weights:', features * weights)
    # print('========================')
    return features * weights

  # Returns a counter of features for the state
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  # Normally weights do not depend on gamestate.  They can be a counter or a dictionary.
  def getWeights(self, gameState, action):
    return {'sucessorScore': 1.0}

class OffensiveAgentZ(AgentZero):

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()
    features['successorScore'] = len(foodList)

    # Distance to nearest food
    if len(foodList) > 0:
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance

    # Deposit priority
    if (myState.numCarrying > 0):
      # Closest distance to base
      depositDist = self.getMazeDistance(myPos, self.basePos)
      dpstPriority = myState.numCarrying * depositDist
      features['dpstPriority'] = dpstPriority

    # Proximity to nearest enemy ghost when pacman
    if myState.isPacman:
      enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
      ghosts = [x for x in enemies if not x.isPacman and x.scaredTimer == 0 and x.getPosition() != None]
      features['numGhosts'] = len(ghosts)
      if len(ghosts) > 0:
        dists = [self.getMazeDistance(myPos, x.getPosition()) for x in ghosts]
        features['ghostDistance'] = min(dists)

    # Avoid reversing or stopping if affordable
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    
    return features

  def getWeights(self, gameState, action):
    # print('===== Ally Offense =====')
    return {'numGhosts': -500, 'ghostDistance': 6, 'dpstPriority': -1, 'successorScore': -100, 'distanceToFood': -3, 'reverse': -2, 'stop': -1000}

class DefensiveAgentZ(AgentZero):
  
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)

    if len(invaders) > 0:
      # print("invador alert")
      howFarAwayInvaders = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      closestInvader = min(howFarAwayInvaders)
      features['invaderDistance'] = closestInvader
    else:
      capsulePosition = self.getCapsulesYouAreDefending(successor)
      howFarAwayCapsule = self.getMazeDistance(myPos, capsulePosition[0])
      features['capsuleDistance'] = howFarAwayCapsule
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    # print('===== Ally Defense =====')
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -100, 'stop': -200, 'reverse': -2, 'capsuleDistance':-10}


# ###############
# # Dummy Agent #
# ###############

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

