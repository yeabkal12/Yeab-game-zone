document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // Views
    const lobbyView = document.getElementById('lobby-view');
    const createGameView = document.getElementById('create-game-view');
    const confirmModalOverlay = document.getElementById('confirm-modal-overlay');

    // Create Game Elements
    const customStakeInput = document.getElementById('custom-stake-input');
    const showConfirmBtn = document.getElementById('show-confirm-btn');

    // Modal Elements
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelConfirmBtn = document.getElementById('cancel-confirm-btn');
    const confirmCreateBtn = document.getElementById('confirm-create-btn');

    // Summary Elements
    const summaryStake = document.getElementById('summary-stake');
    const summaryWin = document.getElementById('summary-win');
    const summaryPrize = document.getElementById('summary-prize');

    let selectedStake = 50;
    let selectedWin = 2;

    // ... (All the other functions like showView and fetchGames remain the same)

    // --- Event Listeners ---

    // When custom input is used, deselect preset buttons
    customStakeInput.addEventListener('input', () => {
        if (customStakeInput.value) {
            const activeButton = stakeOptions.querySelector('.active');
            if (activeButton) activeButton.classList.remove('active');
            selectedStake = customStakeInput.value;
        }
    });
    
    // When preset is clicked, clear custom input
    stakeOptions.addEventListener('click', e => {
        if (e.target.classList.contains('option-btn')) {
            customStakeInput.value = '';
        }
    });

    // Show the confirmation modal
    showConfirmBtn.addEventListener('click', () => {
        // Use custom stake if provided, otherwise use the selected preset
        const stakeValue = customStakeInput.value || selectedStake;
        
        // Validate
        if (!stakeValue || isNaN(stakeValue) || stakeValue <= 0) {
            tg.showAlert('Please enter a valid stake amount.');
            return;
        }
        
        selectedStake = parseInt(stakeValue);
        const prizeValue = (selectedStake * 2 * 0.9).toFixed(2); // Calculate prize with 10% commission

        // Populate summary
        summaryStake.textContent = `${selectedStake} ETB`;
        summaryWin.textContent = `${selectedWin} Piece${selectedWin > 1 ? 's' : ''}`;
        summaryPrize.textContent = `${prizeValue} ETB`;
        
        confirmModalOverlay.classList.remove('hidden');
    });

    // Hide the confirmation modal
    function hideModal() {
        confirmModalOverlay.classList.add('hidden');
    }
    closeModalBtn.addEventListener('click', hideModal);
    cancelConfirmBtn.addEventListener('click', hideModal);

    // Send the final data to the bot
    confirmCreateBtn.addEventListener('click', () => {
        const data = `create_game_stake_${selectedStake}_win_${selectedWin}`;
        tg.sendData(data);
        tg.close();
    });

    // ... (The rest of your event listeners for newGameBtn, cancelCreateBtn, winOptions, etc.)
});