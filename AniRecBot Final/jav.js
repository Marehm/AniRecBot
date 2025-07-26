<script>
	const bgMusic = document.getElementId('bg-music');
	const muteBtn = document.getElementId('muteBtn');

	muteBtn.addEventListener('click', () => {
		if (bgMusic.muted) {
			bgMusic.muted = false;
			muteBtn.textContent = 'Mute';
		} else {
			bgMusic.muted = true;
			muteBtn.textContent = 'Unmute';
		}
	});
</script>