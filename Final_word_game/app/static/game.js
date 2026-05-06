const socket = io();
const config = window.GAME_CONFIG;

const lobbyCode = config.lobbyCode;
const username = config.username;
const userId = config.userId;

const player1Id = config.player1Id;
const player2Id = config.player2Id;

const player1Name = config.player1Name;
const player2Name = config.player2Name;

let wordLength = config.wordLength;

let currentGameState = config.gameState;
let currentTurn = config.currentTurn;

let player1Word = config.player1Word;
let player2Word = config.player2Word;

let player1Guesses = config.player1Guesses || [];
let player2Guesses = config.player2Guesses || [];