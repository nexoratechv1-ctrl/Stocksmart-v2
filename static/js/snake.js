// Snake Game for MultiStore
(function() {
    // Canvas and game settings
    const canvas = document.getElementById('snakeCanvas');
    const ctx = canvas.getContext('2d');
    const scoreSpan = document.getElementById('score');
    
    // Game variables
    let snake = [
        {x: 200, y: 200},
        {x: 190, y: 200},
        {x: 180, y: 200},
        {x: 170, y: 200},
        {x: 160, y: 200}
    ];
    let direction = 'RIGHT';
    let nextDirection = 'RIGHT';
    let food = {};
    let score = 0;
    let gameLoop = null;
    let gameRunning = true;
    const gridSize = 10;      // movement step in pixels
    const canvasSize = 400;
    
    // Initialize random food position
    function randomFood() {
        const cols = canvasSize / gridSize;
        const rows = canvasSize / gridSize;
        let newFood = {
            x: Math.floor(Math.random() * cols) * gridSize,
            y: Math.floor(Math.random() * rows) * gridSize
        };
        // Avoid placing food on snake
        for (let segment of snake) {
            if (segment.x === newFood.x && segment.y === newFood.y) {
                return randomFood();
            }
        }
        return newFood;
    }
    
    // Draw game objects
    function draw() {
        // Clear canvas
        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, canvasSize, canvasSize);
        
        // Draw snake body
        ctx.fillStyle = '#48A9A6';
        for (let i = 0; i < snake.length; i++) {
            ctx.fillRect(snake[i].x, snake[i].y, gridSize-1, gridSize-1);
        }
        // Draw head in gold color
        ctx.fillStyle = '#ffd700';
        ctx.fillRect(snake[0].x, snake[0].y, gridSize-1, gridSize-1);
        
        // Draw food
        ctx.fillStyle = '#ff6666';
        ctx.fillRect(food.x, food.y, gridSize-1, gridSize-1);
    }
    
    // Update game state
    function update() {
        if (!gameRunning) return;
        
        // Apply queued direction
        direction = nextDirection;
        
        // Calculate new head position
        let newHead = {x: snake[0].x, y: snake[0].y};
        switch(direction) {
            case 'RIGHT': newHead.x += gridSize; break;
            case 'LEFT':  newHead.x -= gridSize; break;
            case 'UP':    newHead.y -= gridSize; break;
            case 'DOWN':  newHead.y += gridSize; break;
        }
        
        // Wall collision
        if (newHead.x < 0 || newHead.x >= canvasSize || newHead.y < 0 || newHead.y >= canvasSize) {
            gameOver();
            return;
        }
        
        // Self collision
        let selfCollision = false;
        for (let i = 0; i < snake.length; i++) {
            if (newHead.x === snake[i].x && newHead.y === snake[i].y) {
                selfCollision = true;
                break;
            }
        }
        if (selfCollision) {
            gameOver();
            return;
        }
        
        // Check if food is eaten
        let ateFood = (newHead.x === food.x && newHead.y === food.y);
        
        // Add new head
        snake.unshift(newHead);
        if (!ateFood) {
            snake.pop();
        } else {
            score++;
            scoreSpan.innerText = score;
            food = randomFood();
        }
        
        draw();
    }
    
    function gameOver() {
        if (!gameRunning) return;
        gameRunning = false;
        if (gameLoop) clearInterval(gameLoop);
        gameLoop = null;
        // Get language from page attribute or default to English
        const lang = document.documentElement.lang || 'en';
        const message = (lang === 'sw') ? `Game Over! Alama yako: ${score}` : `Game Over! Your score: ${score}`;
        alert(message);
    }
    
    function restartGame() {
        // Reset game state
        snake = [
            {x: 200, y: 200},
            {x: 190, y: 200},
            {x: 180, y: 200},
            {x: 170, y: 200},
            {x: 160, y: 200}
        ];
        direction = 'RIGHT';
        nextDirection = 'RIGHT';
        score = 0;
        scoreSpan.innerText = '0';
        gameRunning = true;
        food = randomFood();
        if (gameLoop) clearInterval(gameLoop);
        gameLoop = setInterval(update, 100);
        draw();
    }
    
    // Keyboard controls
    function handleKeydown(e) {
        const key = e.key;
        e.preventDefault();
        if (!gameRunning) return;
        if (key === 'ArrowRight' && direction !== 'LEFT') {
            nextDirection = 'RIGHT';
        } else if (key === 'ArrowLeft' && direction !== 'RIGHT') {
            nextDirection = 'LEFT';
        } else if (key === 'ArrowUp' && direction !== 'DOWN') {
            nextDirection = 'UP';
        } else if (key === 'ArrowDown' && direction !== 'UP') {
            nextDirection = 'DOWN';
        }
    }
    
    // Start the game
    function init() {
        food = randomFood();
        draw();
        if (gameLoop) clearInterval(gameLoop);
        gameLoop = setInterval(update, 100);
        window.addEventListener('keydown', handleKeydown);
        
        const restartBtn = document.getElementById('restartBtn');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                restartGame();
            });
        }
    }
    
    // Wait for DOM to load before starting
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
