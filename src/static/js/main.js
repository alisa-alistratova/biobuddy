// Function to toggle favorite status of a paper
async function toggleFavorite(btn, paperId) {
    // 1. Send request to server to toggle favorite status
    try {
        const response = await fetch('/api/toggle_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ paper_id: paperId })
        });

        if (response.ok) {
            const result = await response.json();

            // 2. Update button appearance based on new status
            if (result.is_active) {
                btn.textContent = '★';
                btn.classList.remove('outline');
            } else {
                btn.textContent = '☆';
                btn.classList.add('outline');
            }
        } else {
            alert("Please log in to save favorites.");
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
