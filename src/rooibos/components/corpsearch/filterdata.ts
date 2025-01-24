import { 
    MapPin, Award, Users, TrendingUp, DollarSign, Scale,
    UserPlus, History, Landmark, CalendarDays, Building2, Ban,
    RotateCcw, Check, Sliders
  } from 'lucide-svelte';

  export const filterGroups = [
    {
      id: 'radius',
      title: '반경',
      icon: MapPin,
      iconClass: "text-red-500",
      isMulti: false,
      defaultValue: '200',
      checked: true,
      options: [
        { id: '200', label: '200m' },
        { id: '500', label: '500m' },
        { id: '1000', label: '1km' },
        { id: '2000', label: '2km' },
      ],
    },
    {
      id: 'certification',
      title: '기업 인증',
      icon: Award,
      iconClass: "text-purple-600",
      isMulti: true,
      checked: false,
      options: [
        { id: 'research_institute', label: '연구소 인증' },
        { id: 'venture', label: '벤처 인증' },
        { id: 'innobiz', label: '이노비즈 인증' },
        { id: 'mainbiz', label: '메인비즈 인증' },
        // { id: 'patent', label: '특허 보유' },
        // { id: 'new_technology', label: '신기술' },
      ],
    },
    {
      id: 'employee_count',
      title: '종업원 수',
      icon: Users,
      iconClass: "text-purple-600",
      isMulti: false,
      checked: false,
      options: [
        { id: 'range', label: '명 (범위 설정 가능)' },
      ],
    },
    {
      id: 'sales',
      title: '매출 관련',
      icon: TrendingUp,
      iconClass: "text-green-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'range', label: '숫자를 직접 입력' },
      ],
    },
    {
      id: 'profit',
      title: '영업이익',
      icon: DollarSign,
      iconClass: "text-pink-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'range', label: '숫자를 직접 입력' },
      ],
    },
    {
      id: 'net_profit',
      title: '당기순이익',
      icon: Scale,
      iconClass: "text-pink-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'range', label: '숫자를 직접 입력' },
      ],
    },
    {
      id: 'gender',
      title: '대표 정보',
      icon: UserPlus,
      iconClass: "text-indigo-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'male', label: '남자' },
        { id: 'female', label: '여자' },
      ],
    },
    {
      id: 'gender_age',
      title: '대표의 나이',
      icon: History,
      iconClass: "text-indigo-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'age_input', label: '나이 입력' },
      ],
    },
    {
      id: 'unallocated_profit',
      title: '미처분 이익 잉여금',
      icon: Landmark,
      iconClass: "text-green-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'range', label: '숫자를 직접 입력' },
      ],
    },
    {
      id: 'establishment_year',
      title: '법인 설립 연도',
      icon: CalendarDays,
      iconClass: "text-pink-500",
      isMulti: false,
      checked: false,
      options: [
        { id: 'input_year', label: '직접 입력' },
      ],
    },
    // {
    //   id: 'loan',
    //   title: '대출 사용 여부 및 금액',
    //   icon: Building2,
    //   iconClass: "text-blue-500",
    //   isMulti: false,
    //   options: [
    //     { id: 'use_loan', label: '대출 사용' },
    //     { id: 'no_loan', label: '대출 미사용' },
    //     { id: 'under_100m', label: '대출 1억 이하' },
    //     { id: '100m_to_200m', label: '대출 1억 이상 ~ 2억' },
    //     { id: 'over_200m', label: '2억 이상' },
    //   ],
    // },
    {
      id: 'excluded_industries',
      title: '제외 업종',
      icon: Ban,
      iconClass: "text-red-500",
      isMulti: true,
      checked: false,
      options: [
        { id: 'L6812', label: '임대업' },
        { id: 'L6810', label: '부동산업' },
        { id: 'F4', label: '건설업' },
        { id: 'I5621', label: '유통업' },
      ],
    },
];

export const filterActions = [
    {
      id: 'reset',
      label: '초기화',
      icon: RotateCcw,
      iconClass: "text-gray-500",
      action: 'reset',
    }
];