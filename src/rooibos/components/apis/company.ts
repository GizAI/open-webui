// company.ts
import { WEBUI_API_BASE_URL } from '$lib/constants';

/**
 * 나의기업(북마크)을 삭제하는 함수
 * @param id 삭제할 북마크 ID
 * @returns 성공 여부와 응답 데이터를 포함한 객체
 */
export const deleteCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/softdelete`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Delete failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in deleteCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while deleting the bookmark.' };
  }
};

/**
 * 나의기업(북마크)을 영구적으로 삭제하는 함수
 * @param id 삭제할 북마크 ID
 * @returns 성공 여부와 응답 데이터를 포함한 객체
 */
export const permanentDeleteCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Permanent delete failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in permanentDeleteCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while permanently deleting the bookmark.' };
  }
};

/**
 * 휴지통에서 나의기업(북마크)을 복원하는 함수
 * @param id 복원할 북마크 ID
 * @returns 성공 여부와 응답 데이터를 포함한 객체
 */
export const restoreCompanyBookmark = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
  try {
    const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/restore`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (response.ok) {
      return { success: true, data };
    } else {
      console.error('Restore failed:', data);
      return { success: false, error: data.error || 'Unknown error', data };
    }
  } catch (error) {
    console.error('Error in restoreCompanyBookmark:', error);
    return { success: false, error: 'An unexpected error occurred while restoring the bookmark.' };
  }
};




  
