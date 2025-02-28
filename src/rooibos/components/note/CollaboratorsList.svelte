<script>
  export let users = [];
</script>

<div class="collaborators-list">
  {#if users.length > 0}
    <div class="collaborators-container">
      {#each users as user (user.id)}
        <div class="collaborator-avatar" 
             style="background-color: {user.color}; 
                    {user.avatar ? `background-image: url(${user.avatar})` : ''}">
          {#if !user.avatar}
            {user.name.charAt(0).toUpperCase()}
          {/if}
          <span class="collaborator-tooltip">{user.name}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .collaborators-list {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 100;
  }
  
  .collaborators-container {
    display: flex;
    flex-direction: row-reverse;
  }
  
  .collaborator-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    margin-left: -8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    background-size: cover;
    background-position: center;
    position: relative;
    border: 2px solid white;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    transition: transform 0.2s;
  }
  
  .collaborator-avatar:hover {
    transform: translateY(-3px);
    z-index: 10;
  }
  
  .collaborator-tooltip {
    position: absolute;
    bottom: -30px;
    left: 50%;
    transform: translateX(-50%);
    background-color: #333;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.2s, visibility 0.2s;
  }
  
  .collaborator-avatar:hover .collaborator-tooltip {
    opacity: 1;
    visibility: visible;
  }
</style>