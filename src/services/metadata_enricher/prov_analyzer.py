from collections import Counter
from datetime import datetime
import json

from dishka import Provider, Scope, provide




class ProvAnalyzer:
    def __init__(self):
        self.data = None
        # Risolvi i prefissi
        self.prefixes = None

    
    def _normalize_entity_data(self, entity_data):
        """Normalizza i dati dell'entità, gestendo sia liste che dizionari"""
        if isinstance(entity_data, list):
            # Se è una lista, combina tutti i dizionari in uno solo
            normalized = {}
            for item in entity_data:
                if isinstance(item, dict):
                    normalized.update(item)
            return normalized
        elif isinstance(entity_data, dict):
            return entity_data
        else:
            return {}

    
    def _extract_type(self, data):
        """Estrae il tipo da dati normalizzati"""
        prov_type = data.get('prov:type', 'unknown')
        if isinstance(prov_type, dict):
            return prov_type.get('$', 'unknown')
        elif isinstance(prov_type, list):
            return prov_type[0] if prov_type else 'unknown'
        return str(prov_type)

        
    def resolve_uri(self, prefixed_name):
        """Converte ex:dataset1 in http://example.org/dataset1"""
        if ':' in prefixed_name:
            prefix, local = prefixed_name.split(':', 1)
            if prefix in self.prefixes:
                return self.prefixes[prefix] + local
        return prefixed_name
    
    def extract_comprehensive_summary(self):
        """Estrae un sommario completo per LLM"""
        summary = {
            'overview': self.get_overview(),
            'entities': self.analyze_entities(),
            'activities': self.analyze_activities(), 
            'agents': self.analyze_agents(),
            'relationships': self.analyze_relationships(),
            'temporal_info': self.extract_temporal_info(),
            'key_insights': self.extract_key_insights(),
            'provenance_patterns': self.identify_patterns()
        }
        return summary
    
    def get_overview(self):
        """Statistiche generali"""
        return {
            'total_entities': len(self.data.get('entity', {})),
            'total_activities': len(self.data.get('activity', {})),
            'total_agents': len(self.data.get('agent', {})),
            'total_relationships': sum(len(v) for k, v in self.data.items() 
                                    if k not in ['entity', 'activity', 'agent', 'prefix', 'bundle']),
            'namespaces_used': list(self.prefixes.keys()),
            'has_bundles': 'bundle' in self.data and len(self.data['bundle']) > 0
        }
    
    def analyze_entities(self):
        """Analisi dettagliata delle entità - FIXED VERSION"""
        entities = self.data.get('entity', {})
        entity_analysis = {
            'count': len(entities),
            'types': Counter(),
            'attributes': Counter(),
            'examples': []
        }
        
        for eid, entity_data in entities.items():
            # Normalizza i dati dell'entità (ovvero se sono in formato lista li trasforma in formato dizionario)
            normalized_data = self._normalize_entity_data(entity_data)
            
            # Conta i tipi
            entity_type = self._extract_type(normalized_data)
            entity_analysis['types'][entity_type] += 1
            
            # Conta gli attributi
            for attr in normalized_data.keys():
                entity_analysis['attributes'][attr] += 1
            
            # Salva esempi interessanti
            if len(entity_analysis['examples']) < 6:
                entity_analysis['examples'].append({
                    'id': eid,
                    'full_uri': self.resolve_uri(eid),
                    'type': entity_type,
                    'attributes': list(normalized_data.keys()),
                    'raw_data_type': type(entity_data).__name__  # Debug info
                })
        
        return entity_analysis
    
    def analyze_activities(self):
        """per ogni attivita si fa una breve analisi e si danno esempi"""
        activities = self.data.get('activity', {})
        activity_analysis = {
            'count': len(activities),
            'types': Counter(),
            'duration_info': [],
            'examples': []
        }
        
        for aid, activity_data in activities.items():
            # Normalizza i dati dell'attività
            normalized_data = self._normalize_entity_data(activity_data)
            
            # Tipo attività
            activity_type = self._extract_type(normalized_data)
            activity_analysis['types'][activity_type] += 1
            
            # Info temporali
            start_time = normalized_data.get('prov:startTime')
            end_time = normalized_data.get('prov:endTime')
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
                    duration = end_dt - start_dt
                    activity_analysis['duration_info'].append({
                        'activity': aid,
                        'duration_seconds': duration.total_seconds()
                    })
                except Exception as e:
                    pass
            
            # Esempi
            if len(activity_analysis['examples']) < 3:
                activity_analysis['examples'].append({
                    'id': aid,
                    'type': activity_type,
                    'has_timing': bool(start_time or end_time),
                    'attributes': list(normalized_data.keys())
                })
        
        return activity_analysis
    
    def analyze_agents(self):
        """Analisi degli agenti - FIXED VERSION"""
        agents = self.data.get('agent', {})
        agent_analysis = {
            'count': len(agents),
            'types': Counter(),
            'examples': []
        }
        
        for agent_id, agent_data in agents.items():
            # Normalizza i dati dell'agente
            normalized_data = self._normalize_entity_data(agent_data)
            
            agent_type = self._extract_type(normalized_data)
            agent_analysis['types'][agent_type] += 1
            
            if len(agent_analysis['examples']) < 3:
                agent_analysis['examples'].append({
                    'id': agent_id,
                    'type': agent_type,
                    'attributes': list(normalized_data.keys())
                })
        
        return agent_analysis
    
    def analyze_relationships(self):
        """Analisi delle relazioni"""
        relationships = {}
        relation_types = [
            'used', 'wasGeneratedBy', 'wasDerivedFrom', 'wasAttributedTo',
            'wasAssociatedWith', 'wasInformedBy', 'wasStartedBy', 'wasEndedBy',
            'wasInvalidatedBy', 'actedOnBehalfOf', 'wasInfluencedBy',
            'specializationOf', 'alternateOf', 'hadMember'
        ]
        
        for rel_type in relation_types:
            if rel_type in self.data:
                rel_data = self.data[rel_type]
                if isinstance(rel_data, dict):
                    relationships[rel_type] = {
                        'count': len(rel_data),
                        'examples': []
                    }
                    
                    # Prendi alcuni esempi
                    for i, (rel_id, rel_props) in enumerate(rel_data.items()):
                        if i < 2:  # Massimo 2 esempi per tipo
                            normalized_props = self._normalize_entity_data(rel_props)
                            relationships[rel_type]['examples'].append({
                                'id': rel_id,
                                'properties': normalized_props
                            })
        
        return relationships
    
    def extract_temporal_info(self):
        """Estrae informazioni temporali - IMPROVED VERSION"""
        temporal_info = {
            'time_ranges': [],
            'chronological_activities': []
        }
        
        # Cerca timestamp in attività e relazioni
        all_times = []
        
        # Tempi dalle attività
        for aid, activity in self.data.get('activity', {}).items():
            normalized_activity = self._normalize_entity_data(activity)
            for time_key in ['prov:startTime', 'prov:endTime']:
                if time_key in normalized_activity:
                    try:
                        time_val = str(normalized_activity[time_key])
                        dt = datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                        all_times.append((dt, aid, time_key))
                    except Exception:
                        pass
        
        # Tempi dalle relazioni
        for rel_type, relations in self.data.items():
            if isinstance(relations, dict) and rel_type not in ['entity', 'activity', 'agent', 'prefix', 'bundle']:
                for rel_id, rel_data in relations.items():
                    normalized_rel = self._normalize_entity_data(rel_data)
                    if 'prov:time' in normalized_rel:
                        try:
                            time_val = str(normalized_rel['prov:time'])
                            dt = datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                            all_times.append((dt, rel_id, 'prov:time'))
                        except Exception:
                            pass
        
        # Ordina cronologicamente
        all_times.sort()
        temporal_info['chronological_events'] = [
            {
                'timestamp': dt.isoformat(),
                'element_id': elem_id,
                'time_type': time_type
            }
            for dt, elem_id, time_type in all_times[:10]  # Prime 10 per brevità
        ]
        
        if all_times:
            temporal_info['time_range'] = {
                'earliest': all_times[0][0].isoformat(),
                'latest': all_times[-1][0].isoformat()
            }
        
        return temporal_info
    
    def extract_key_insights(self):
        """Estrae insight chiave - IMPROVED VERSION"""
        insights = []
        
        # Trova entità con molte derivazioni
        derivations = self.data.get('wasDerivedFrom', {})
        derived_from_count = Counter()
        derived_to_count = Counter()
        
        for rel_data in derivations.values():
            normalized_rel = self._normalize_entity_data(rel_data)
            used_entity = normalized_rel.get('prov:usedEntity')
            generated_entity = normalized_rel.get('prov:generatedEntity')
            if used_entity:
                derived_from_count[used_entity] += 1
            if generated_entity:
                derived_to_count[generated_entity] += 1
        
        if derived_from_count:
            most_used = derived_from_count.most_common(1)[0]
            insights.append(f"Most influential source entity: {most_used[0]} (used in {most_used[1]} derivations)")
        
        if derived_to_count:
            most_derived = derived_to_count.most_common(1)[0]
            insights.append(f"Most derived entity: {most_derived[0]} (derived {most_derived[1]} times)")
        
        # Trova agenti più attivi
        attributions = self.data.get('wasAttributedTo', {})
        associations = self.data.get('wasAssociatedWith', {})
        
        agent_activity = Counter()
        for rel_data in attributions.values():
            normalized_rel = self._normalize_entity_data(rel_data)
            agent = normalized_rel.get('prov:agent')
            if agent:
                agent_activity[agent] += 1
        
        for rel_data in associations.values():
            normalized_rel = self._normalize_entity_data(rel_data)
            agent = normalized_rel.get('prov:agent')
            if agent:
                agent_activity[agent] += 1
        
        if agent_activity:
            most_active = agent_activity.most_common(1)[0]
            insights.append(f"Most active agent: {most_active[0]} (involved in {most_active[1]} activities)")
        
        return insights
    
    def identify_patterns(self):
        """Identifica pattern comuni"""
        patterns = []
        
        # Pattern: Pipeline sequenziale
        generations = self.data.get('wasGeneratedBy', {})
        usages = self.data.get('used', {})
        
        if len(generations) > 1 and len(usages) > 1:
            patterns.append("Sequential data processing pipeline detected")
        
        # Pattern: Collaborazione multipla
        agents = len(self.data.get('agent', {}))
        if agents > 2:
            patterns.append("Multi-agent collaboration workflow")
        
        # Pattern: Versioning
        entities = self.data.get('entity', {})
        versions = [e for e in entities.keys() if any(v in str(e).lower() for v in ['v1', 'v2', 'version', 'rev'])]
        if versions:
            patterns.append("Entity versioning detected")
        
        return patterns
    


















    def debug_data_structure(self, provenance):
        self.data=provenance
        
        """Metodo di debug per capire la struttura dei dati"""
        debug_info = {}
        
        for section in ['entity', 'activity', 'agent']:
            if section in self.data:
                section_data = self.data[section]
                debug_info[section] = {
                    'count': len(section_data),
                    'sample_keys': list(section_data.keys())[:8],
                    'sample_data_types': {}
                }
                
                for key, value in list(section_data.items())[:3]:
                    debug_info[section]['sample_data_types'][key] = type(value).__name__
                    if isinstance(value, list) and value:
                        debug_info[section]['sample_data_types'][f"{key}_first_item"] = type(value[0]).__name__
        
        return json.dumps(debug_info)
    

    






    def generate_simple_llm_context(self, provenance):
        self.data=provenance
        self.prefixes=self.data.get('prefix', {})
        
        summary = self.extract_comprehensive_summary()
        
        context = f"""PROV-JSON Analysis:

            OVERVIEW:
            - {summary['overview']['total_entities']} entities, {summary['overview']['total_activities']} activities, {summary['overview']['total_agents']} agents
            - Namespaces: {', '.join(summary['overview']['namespaces_used'])}

            ENTITIES: {dict(summary['entities']['types'])}
            ACTIVITIES: {dict(summary['activities']['types'])}

            KEY RELATIONSHIPS:
        """
        
        for rel_type, rel_info in summary['relationships'].items():
            context += f"- {rel_type}: {rel_info['count']} instances\n"
        
        if summary['temporal_info'].get('time_range'):
            context += f"\nTIME RANGE: {summary['temporal_info']['time_range']['earliest']} to {summary['temporal_info']['time_range']['latest']}\n"
        
        context += f"\nKEY INSIGHTS:\n"
        for insight in summary['key_insights']:
            context += f"- {insight}\n"
        
        return context
    









class AnalyzerProvider(Provider):
    @provide(scope=Scope.APP)
    def analyzer_provider(self)->ProvAnalyzer:
        return ProvAnalyzer()
    




