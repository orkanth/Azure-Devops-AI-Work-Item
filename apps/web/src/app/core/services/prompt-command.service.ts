import { Injectable } from '@angular/core';
import { PromptProposal, WorkItem, WorkItemActionKind, WorkItemState, WorkItemType } from '../../shared/models/work-item.model';

@Injectable({ providedIn: 'root' })
export class PromptCommandService {
  interpret(prompt: string, items: WorkItem[]): PromptProposal {
    const text = prompt.trim();
    if (!text) return this.unknown('Enter a command to get started.');

    const createMatch = text.match(/\b(create|add|make|generate)\b/i);
    if (createMatch) return this.createProposal(text);

    const assignMatch = text.match(/\b(assign|reassign)\b/i);
    if (assignMatch) return this.targetedProposal(text, items, 'assign');

    const deleteMatch = text.match(/\b(delete|remove)\b/i);
    if (deleteMatch) return this.targetedProposal(text, items, 'delete');

    const updateMatch = text.match(/\b(update|edit|change|move|mark|set|rename|complete|finish|close|start)\b/i);
    if (updateMatch) return this.targetedProposal(text, items, 'update');

    return this.unknown('I could not identify a work-item action. Try create, update, assign, or delete in your prompt.');
  }

  private createProposal(text: string): PromptProposal {
    const type = this.inferType(text);
    const title = this.inferCreateTitle(text, type);
    if (!type) {
      return this.unknown('Please specify the work-item type: Epic, Feature, User Story, or Task.');
    }
    if (!title) {
      return this.unknown(`I know you want to create a ${type}, but I need a title. For example: "Create a ${type.toLowerCase()} for password reset."`);
    }
    return {
      kind: 'create',
      description: `Create ${type === 'Epic' ? 'an' : 'a'} ${type} called “${title}”`,
      newItem: { type, title, state: 'New', assignedTo: 'Unassigned', priority: 'Medium' },
    };
  }

  private targetedProposal(text: string, items: WorkItem[], action: WorkItemActionKind): PromptProposal {
    const targetResolution = this.resolveTarget(text, items, action);
    if (targetResolution.kind === 'ambiguous') {
      return {
        kind: 'ambiguous',
        actionKind: action,
        candidates: targetResolution.candidates,
        description: 'More than one work item may match. Choose the exact item before continuing.',
        error: 'Ambiguous work-item reference',
        ...(action === 'assign' ? { assignee: this.extractAssignee(text) } : {}),
        ...(action === 'update' ? { changes: this.extractChanges(text) } : {}),
      };
    }
    if (!targetResolution.target) {
      return this.unknown(targetResolution.error ?? 'I could not find the work item. Include its ID, for example #104.');
    }

    const target = targetResolution.target;
    if (action === 'delete') {
      return { kind: 'delete', target, description: `Delete ${target.type} #${target.id}: “${target.title}”` };
    }
    if (action === 'assign') {
      const assignee = this.extractAssignee(text);
      if (!assignee) return this.unknown('Please include the user to assign, for example: "Assign task #104 to Alex Morgan."');
      return { kind: 'assign', target, assignee, description: `Assign ${target.type} #${target.id} to ${assignee}` };
    }

    const changes = this.extractChanges(text);
    if (!Object.keys(changes).length) {
      return this.unknown('I could identify the work item, but not the change. Try changing its state or use "rename #104 to API validation tests".');
    }
    const changeText = changes.state ? `set the state to ${changes.state}` : changes.title ? `rename it to “${changes.title}”` : 'update its details';
    return { kind: 'update', target, changes, description: `Update ${target.type} #${target.id}: ${changeText}` };
  }

  private resolveTarget(text: string, items: WorkItem[], action: WorkItemActionKind): { target?: WorkItem; kind?: 'ambiguous'; candidates?: WorkItem[]; error?: string } {
    const idMatch = text.match(/#(\d+)\b/) ?? text.match(/\b(?:task|story|epic|feature|work item)\s+(\d+)\b/i);
    if (idMatch) {
      const id = Number(idMatch[1]);
      const target = items.find((item) => item.id === id);
      return target ? { target } : { error: `Work item #${id} was not found in the current list.` };
    }

    let targetText = text
      .replace(/^\s*(please\s+)?(delete|remove|update|edit|change|move|mark|set|rename|complete|finish|close|start|assign|reassign)\s+/i, '')
      .replace(/\b(to|as)\s+(done|complete|completed|closed|close|finish|finished|resolved|active|in progress|new|to do)\b.*$/i, '')
      .replace(/\bto\s+.+$/i, '')
      .replace(/\b(?:called|named|titled)\b/gi, ' ')
      .replace(/\b(the|a|an|task|tasks|epic|epics|feature|features|story|stories|user story|work item|work items|item)\b/gi, ' ')
      .replace(/\b(status|state|title|name|assignee)\b/gi, ' ')
      .replace(/[^a-zA-Z0-9\s-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();

    const stopWords = new Set(['please', 'the', 'a', 'an', 'to', 'for', 'of', 'with', 'its', 'it', 'in', 'from', 'on', 'as', 'is', 'be', 'change', 'update', 'edit', 'move', 'mark', 'set', 'rename', 'complete', 'finish', 'close', 'start', 'called', 'named', 'titled', 'assign', 'reassign', 'delete', 'remove']);
    const tokens = targetText.split(' ').filter((token) => token.length > 1 && !stopWords.has(token));
    if (!tokens.length) return { error: 'Please identify the item by ID or enough of its title. Example: "Update #104 to Active".' };

    const scored = items.map((item) => {
      const title = item.title.toLowerCase();
      const titleTokens = title.split(/[^a-z0-9]+/).filter(Boolean);
      const matched = tokens.filter((token) => title.includes(token) || titleTokens.some((titleToken) => titleToken.startsWith(token))).length;
      const score = matched / tokens.length;
      return { item, score, matched };
    }).filter((entry) => entry.matched > 0).sort((a, b) => b.score - a.score || b.matched - a.matched);

    if (!scored.length) return { error: `I could not find a work item matching “${targetText}”. Include its exact ID, such as #104.` };
    const best = scored[0];
    if (!best) return { error: 'I could not resolve the work item. Please include its ID.' };
    const bestScore = best.score;
    const bestMatches = scored.filter((entry) => entry.score === bestScore && entry.matched === best.matched);
    if (bestMatches.length > 1) return { kind: 'ambiguous', candidates: bestMatches.slice(0, 5).map((entry) => entry.item) };
    return { target: best.item };
  }

  private extractAssignee(text: string): string | undefined {
    const match = text.match(/\bto\s+(.+?)\s*(?:\b(?:in|for)\s+(?:sprint|iteration|project)\b.*)?$/i);
    if (!match) return undefined;
    const rawValue = match[1];
    if (!rawValue) return undefined;
    const value = rawValue.replace(/[.!?]+$/, '').trim();
    return value && !/^(done|completed|closed|resolved|active|in progress|new|to do)$/i.test(value) ? value : undefined;
  }

  private extractChanges(text: string): Partial<WorkItem> {
    const stateRules: Array<[RegExp, WorkItemState]> = [
      [/\b(done|complete|completed|closed|close|finish|finished)\b/i, 'Closed'],
      [/\b(resolved)\b/i, 'Resolved'],
      [/\b(in progress|active|started)\b/i, 'Active'],
      [/\b(to do|new|not started)\b/i, 'New'],
    ];
    for (const [pattern, state] of stateRules) {
      if (pattern.test(text)) return { state };
    }

    const rename = text.match(/\b(?:rename|change|update|edit)\b.*?\b(?:title|name)\b.*?\bto\s+(.+)$/i)
      ?? text.match(/\b(?:rename|edit)\b.*?\bto\s+(.+)$/i);
    if (rename?.[1]) return { title: rename[1].replace(/[.!?]+$/, '').trim() };

    const priorityMatch = text.match(/\bpriority\s+(?:to\s+)?(low|medium|high)\b/i);
    if (priorityMatch?.[1]) {
      const priority = priorityMatch[1].slice(0, 1).toUpperCase() + priorityMatch[1].slice(1).toLowerCase();
      return { priority: priority as WorkItem['priority'] };
    }
    return {};
  }

  private inferType(text: string): WorkItemType | undefined {
    if (/\buser stor(?:y|ies)\b|\bstories\b|\bstory\b/i.test(text)) return 'User Story';
    if (/\bepics?\b/i.test(text)) return 'Epic';
    if (/\bfeatures?\b/i.test(text)) return 'Feature';
    if (/\btasks?\b/i.test(text)) return 'Task';
    return undefined;
  }

  private inferCreateTitle(text: string, type?: WorkItemType): string {
    let title = text
      .replace(/^\s*(please\s+)?(create|add|make|generate)\s+/i, '')
      .replace(/\b(?:a|an|the)\s+/i, ' ');
    if (type) {
      const typePattern = type === 'User Story' ? /\buser stor(?:y|ies)\b|\bstory\b/ig : new RegExp(`\\b${type.toLowerCase()}s?\\b`, 'ig');
      title = title.replace(typePattern, ' ');
    }
    title = title
      .replace(/^\s*(?:for|about|called|named|titled)\s+/i, '')
      .replace(/\bunder\s+.+$/i, '')
      .replace(/\b(?:in azure devops|in the current project)\b.*$/i, '')
      .replace(/[.!?]+$/, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (/^for\s+/i.test(title)) title = title.replace(/^for\s+/i, '').trim();
    return title ? title.slice(0, 1).toUpperCase() + title.slice(1) : '';
  }

  private unknown(error: string): PromptProposal {
    return { kind: 'unknown', description: 'I need a little more detail before I can prepare this change.', error };
  }
}
