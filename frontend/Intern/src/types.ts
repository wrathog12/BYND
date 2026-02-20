export type Article = {
  id: number;
  title: string;
  link: string;
  source: string;
  date: string;
  company_tag: string;
  bucket: string;
  event_label: string;
  full_text: string;
  summary: string;
  word_count: number;
  scrape_method: string;
  status: string;
  duplicates_merged: number;
  created_at: string;
};

export type PipelineResponse = {
  discovered: number;
  filtered: number;
  scraped: number;
  failed: number;
  summarized: number;
  stored: number;
};

export type ArticlesResponse = {
  count: number;
  articles: Article[];
};

export type Bucket = 'FINANCIALS' | 'STRATEGIC_GROWTH' | 'PRODUCT_INNOVATION' | 'LEGAL_AND_RISK';

export const COMPANIES = ['OpenAI', 'Anthropic', 'Google Deepmind', 'Microsoft', 'Meta'] as const;

export const BUCKETS: { key: Bucket; label: string; css: string }[] = [
  { key: 'FINANCIALS', label: 'Financials', css: 'financials' },
  { key: 'STRATEGIC_GROWTH', label: 'Strategic Growth', css: 'strategic_growth' },
  { key: 'PRODUCT_INNOVATION', label: 'Innovation', css: 'product_innovation' },
  { key: 'LEGAL_AND_RISK', label: 'Legal & Risk', css: 'legal_and_risk' },
];

