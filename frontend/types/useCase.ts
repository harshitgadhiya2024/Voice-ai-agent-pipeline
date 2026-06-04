export interface UseCaseIntent {
  id: string;
  label: string;
  description: string;
}

export interface UseCaseMetadata {
  id: string;
  name: string;
  company: string;
  tagline: string;
  description: string;
  icon: string;
  accent: string;
  greeting: string;
  sample_questions: string[];
  knowledge_records?: number;
  intents: UseCaseIntent[];
  default_voice_gender: "female" | "male";
  persona_name_female: string;
  persona_name_male: string;
}
