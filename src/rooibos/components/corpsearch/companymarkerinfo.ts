import { goto } from '$app/navigation';
import { user } from '$lib/stores';
import { WEBUI_API_BASE_URL } from '$lib/constants';
import { selectedCompanyInfo } from '$rooibos/stores';
import { get } from 'svelte/store';

declare global {
  interface Window {
    handleGptClick: (data: any) => void;
    handleFavoriteClick: (data: any, data1: any) => void;
  }
}

export const compayMarkerInfo = (
  result: any
): string => {

  const encodedResult = btoa(encodeURIComponent(JSON.stringify(result)));

  window.handleFavoriteClick = async (encodedResult, resultString) => {
    try {
      const companyData = JSON.parse(decodeURIComponent(atob(encodedResult)));
      const bookmarkCorp = JSON.parse(decodeURIComponent(resultString));
      const currentUser = get(user);
      
      if (!bookmarkCorp.bookmark_id) {
        const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/add`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.token}`
          },
          body: JSON.stringify({ userId: currentUser?.id, companyId: companyData.smtp_id, business_registration_number: companyData.business_registration_number }),
        });
  
        const { data } = await response.json();
        bookmarkCorp.bookmark_id = data.id;
      } else {
        await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${bookmarkCorp.bookmark_id}/delete`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.token}`
          },
      });
      }
    } catch (error) {
      console.error("Error processing data:", error);
    }
  };

  window.handleGptClick = async (encodedData: string) => {
    try {
      const data = JSON.parse(decodeURIComponent(atob(encodedData)));
  
      selectedCompanyInfo.set(data);
      await goto('/');
    } catch (error) {
      console.error('Error processing data:', error);
    }
  };  

  const formatDistance = (distance: number): string => {
    return distance < 1000 ? `${distance}m` : `${(distance / 1000).toFixed(1)}km`;
  };

  return `
      <div style="padding: 16px; max-width: 300px; word-wrap: break-word; font-family: Arial, sans-serif; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 10px;">
          <h3 style="font-size: 16px; font-weight: bold; margin: 0;">
            <span style="color: #2563eb;">${result.company_name}</span>
            <span style="color: #6B7280;">(${result.business_registration_number})</span>
          </h3>
        </div>

        <div style="display: flex; gap: 20px; margin: 5px 0;">
          ${result.representative ?
            `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
              대표자: ${result.representative}${result.birth_date ? ` (${result.birth_date})` : ''}
            </p>` :
            ""
          }
        </div>

        ${result.address ?
          `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            ${result.address}
          </p>` :
          ""}
        ${result.phone_number ?
          `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            ${result.phone_number}
          </p>` :
          ""}

        ${result.industry ?
          `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
            </svg>
            업종: ${result.industry}
          </p>` :
          ""}
        
          ${result.group_name ?
            `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"></path>
                <path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"></path>
              </svg>
              그룹명: ${result.group_name}
            </p>` :
            ""}
  
          ${result.main_product ?
            `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              </svg>
              주요 상품: ${result.main_product}
            </p>` :
            ""}

          <div style="display: flex; gap: 20px; margin: 5px 0;">
            ${result.establishment_date ?
              `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EC4899" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                설립일: ${String(result.establishment_date).replace(/(\d{4})(\d{2})(\d{2})/, '$1.$2.$3')}
              </p>` :
              ""
            }
            ${result.employee_count ?
              `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                임직원: ${result.employee_count}명</p>` :
              ""
            }
          </div>

          <div style="display: flex; gap: 20px; margin: 5px 0;">
            ${result.total_assets ?
              `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                  <line x1="1" y1="10" x2="23" y2="10"></line>
                </svg>
                총자산: ${result.total_assets}억</p>` :
              ""
            }

            ${result.recent_total_equity ?
              `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                총자본: ${result.recent_total_equity}억</p>` :
              ""
            }
          </div>
  
          <div style="display: flex; gap: 20px; margin: 5px 0;">
            ${result.net_income ?
              `<p style="font-size: 13px; margin: 0; display: flex; align-items: center; gap: 5px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="1" x2="12" y2="23"></line>
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>
                당기순이익: ${result.net_income}억</p>` :
              ""
            }
          </div>  

        ${result.website ?
          `<p style="font-size: 13px; margin: 5px 0; display: flex; align-items: center; gap: 5px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#EAB308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            <a href="${result.website.startsWith("http") ? result.website : `https://${result.website}`}" 
                target="_blank" style="color: #2563eb; text-decoration: none;">
                홈페이지
            </a>
          </p>` :
          ""}
        ${result.distance_from_user ?
          `<span style="font-size: 13px; display: flex; align-items: center; gap: 5px; margin: 5px 0;">
            📏 ${formatDistance(result.distance_from_user)}
          </span>` :
          ""}

        <div style="display: flex; gap: 10px; margin-top: 10px; align-items: center;">
          <button style="background: none; border: none; cursor: pointer;"
            onclick="(() => { window.handleFavoriteClick('${encodedResult}', '${encodeURIComponent(JSON.stringify(result))}') })()">
            <img 
              src="${result.id ? '/rooibos/yellowStar.png' : '/rooibos/star.png'}" 
              alt="즐겨찾기" 
              style="width: 20px; height: 20px;"
            />
          </button>
          <button 
            style="background: none; border: none; cursor: pointer;"
            onclick="(() => { window.handleGptClick('${encodedResult}') })()"
          >
            <img 
              src="/rooibos/gpt.ico" 
              alt="GPT 묻기" 
              style="width: 20px; height: 20px;"
            />
          </button>
          <button style="background: none; border: none; cursor: pointer;"
            onclick="window.open('https://map.naver.com/v5/search/${encodeURIComponent(
              result.company_name
            )}', '_blank')">
            <img 
              src="/rooibos/naver.svg" 
              alt="네이버" 
              style="width: 20px; height: 20px;"
            />
          </button>
        </div>
      </div>

    `;
};
