import { PromptCommandService } from './prompt-command.service';

describe('PromptCommandService', () => {
  it('prepares a Bug proposal from a natural-language create prompt', () => {
    const service = new PromptCommandService();

    const proposal = service.interpret('Create a bug for password reset', []);

    expect(proposal.kind).toBe('create');
    expect(proposal.newItem).toMatchObject({
      type: 'Bug',
      title: 'Password reset',
    });
  });
});
