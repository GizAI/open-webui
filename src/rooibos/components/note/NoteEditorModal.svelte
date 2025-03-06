<!-- NoteEditorModal.svelte -->
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import NoteEditor from '$rooibos/components/note/NoteEditor.svelte';

    // Create event dispatcher
    const dispatch = createEventDispatcher();

    // Props
    interface FileInfo {
        id: string;
        name: string;
        [key: string]: any;
    }
    
    export let selectedFile: FileInfo | null = null;
    export let isOpen = false;

    // Handle close event from the editor
    function handleClose() {
        isOpen = false;
        dispatch('close');
    }
</script>

{#if isOpen && selectedFile}
    <NoteEditor 
        {selectedFile} 
        {isOpen} 
        on:close={handleClose} 
        on:titleChange={(e) => dispatch('titleChange', e.detail)}
    />
{/if} 