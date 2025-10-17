import { render, screen } from '@/__tests__/test-utils';
import Home from '../page';

describe('Landing Page', () => {
  it('renders hero section with title and tagline', () => {
    render(<Home />);

    expect(screen.getByText('Pulse')).toBeInTheDocument();
    expect(screen.getByText(/news aggregation with ethical clarity/i)).toBeInTheDocument();
  });

  it('displays main value proposition', () => {
    render(<Home />);

    expect(screen.getByText(/ai-powered summaries/i)).toBeInTheDocument();
    expect(screen.getAllByText(/bias detection/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/framework analysis/i)).toBeInTheDocument();
  });

  it('renders Get Started button with correct link', () => {
    render(<Home />);

    const getStartedButton = screen.getByRole('link', { name: /get started/i });
    expect(getStartedButton).toBeInTheDocument();
    expect(getStartedButton).toHaveAttribute('href', '/signup');
  });

  it('renders Log In button with correct link', () => {
    render(<Home />);

    const loginButton = screen.getByRole('link', { name: /log in/i });
    expect(loginButton).toBeInTheDocument();
    expect(loginButton).toHaveAttribute('href', '/login');
  });

  it('displays all three feature cards', () => {
    render(<Home />);

    expect(screen.getByText('AI Summaries')).toBeInTheDocument();
    expect(screen.getByText('Bias Detection')).toBeInTheDocument();
    expect(screen.getByText('Framework Mapping')).toBeInTheDocument();
  });

  it('shows AI Summaries feature description', () => {
    render(<Home />);

    expect(screen.getByText(/concise 100-word summaries/i)).toBeInTheDocument();
    expect(screen.getByText(/saving you time/i)).toBeInTheDocument();
  });

  it('shows Bias Detection feature description', () => {
    render(<Home />);

    expect(screen.getByText(/sentiment analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/political lean detection/i)).toBeInTheDocument();
  });

  it('shows Framework Mapping feature description', () => {
    render(<Home />);

    expect(screen.getByText(/our unique feature/i)).toBeInTheDocument();
    expect(screen.getByText(/privacy vs\. security/i)).toBeInTheDocument();
  });

  it('renders How It Works section', () => {
    render(<Home />);

    expect(screen.getByText(/how it works/i)).toBeInTheDocument();
  });

  it('displays step-by-step process', () => {
    render(<Home />);

    expect(screen.getByText(/choose your topics/i)).toBeInTheDocument();
    expect(screen.getByText(/we aggregate & analyze/i)).toBeInTheDocument();
    expect(screen.getByText(/daily newsletter delivered/i)).toBeInTheDocument();
  });

  it('shows trusted sources section', () => {
    render(<Home />);

    expect(screen.getByRole('heading', { name: /trusted sources/i })).toBeInTheDocument();
    expect(screen.getByText('Reuters')).toBeInTheDocument();
    expect(screen.getByText('AP News')).toBeInTheDocument();
    expect(screen.getByText('BBC')).toBeInTheDocument();
  });

  it('displays CTA section', () => {
    render(<Home />);

    expect(screen.getByText(/start your free newsletter today/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign up now/i })).toBeInTheDocument();
  });

  it('renders with gradient background', () => {
    const { container } = render(<Home />);

    const mainDiv = container.firstChild as HTMLElement;
    expect(mainDiv).toHaveClass('min-h-screen');
    expect(mainDiv).toHaveClass('bg-gradient-to-br');
  });

  it('has proper semantic structure', () => {
    const { container } = render(<Home />);

    // Should have h1 for main title
    const h1 = container.querySelector('h1');
    expect(h1).toBeInTheDocument();
    expect(h1).toHaveTextContent('Pulse');

    // Should have h2 for "How It Works"
    const h2 = container.querySelector('h2');
    expect(h2).toBeInTheDocument();
    expect(h2).toHaveTextContent('How It Works');

    // Should have h3 for feature titles
    const h3Elements = container.querySelectorAll('h3');
    expect(h3Elements.length).toBeGreaterThan(0);
  });

  it('displays all feature emojis', () => {
    render(<Home />);

    const text = screen.getByText('🤖').textContent;
    expect(text).toBe('🤖');

    const text2 = screen.getByText('⚖️').textContent;
    expect(text2).toBe('⚖️');

    const text3 = screen.getByText('🎯').textContent;
    expect(text3).toBe('🎯');
  });

  it('renders responsive layout classes', () => {
    const { container } = render(<Home />);

    // Check for grid layout
    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('md:grid-cols-3');
  });
});
