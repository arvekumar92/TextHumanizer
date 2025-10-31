import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Copy, Eraser, Sparkles, History, Trash2, Loader2, FileText } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [tone, setTone] = useState("conversational");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [stats, setStats] = useState({ words: 0, chars: 0 });

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`);
      setHistory(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const handleRephrase = async () => {
    if (!inputText.trim()) {
      toast.error("Please enter some text to rephrase");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/rephrase`, {
        text: inputText,
        tone: tone
      });

      setOutputText(response.data.rephrased_text);
      setStats({
        words: response.data.word_count,
        chars: response.data.char_count
      });

      // Save to history
      await axios.post(`${API}/history`, {
        original_text: inputText,
        rephrased_text: response.data.rephrased_text,
        tone: tone
      });

      await fetchHistory();
      toast.success("Text rephrased successfully!");
    } catch (error) {
      console.error("Error rephrasing:", error);
      toast.error("Failed to rephrase text. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (outputText) {
      navigator.clipboard.writeText(outputText);
      toast.success("Copied to clipboard!");
    }
  };

  const handleClear = () => {
    setInputText("");
    setOutputText("");
    setStats({ words: 0, chars: 0 });
    toast.info("Text cleared");
  };

  const deleteHistoryItem = async (id) => {
    try {
      await axios.delete(`${API}/history/${id}`);
      await fetchHistory();
      toast.success("History item deleted");
    } catch (error) {
      console.error("Error deleting history:", error);
      toast.error("Failed to delete history item");
    }
  };

  const loadHistoryItem = (item) => {
    setInputText(item.original_text);
    setOutputText(item.rephrased_text);
    setTone(item.tone);
    toast.info("History item loaded");
  };

  const inputWordCount = inputText.trim() ? inputText.trim().split(/\s+/).length : 0;
  const inputCharCount = inputText.length;

  return (
    <div className="app-container gradient-bg min-h-screen py-8 px-4">
      <Toaster position="top-center" richColors />
      
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 fade-in">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gradient mb-3" data-testid="app-title">
            TextHumanizer
          </h1>
          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto" data-testid="app-subtitle">
            Transform your text with AI-powered rephrasing for perfect grammar and natural flow
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <Card className="main-card glass-effect border-0 shadow-xl" data-testid="main-card">
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <CardTitle className="text-2xl font-bold flex items-center gap-2" data-testid="card-title">
                      <Sparkles className="w-6 h-6 text-teal-600" />
                      Rephrase Your Text
                    </CardTitle>
                    <CardDescription data-testid="card-description">Enter text and choose your preferred tone</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select value={tone} onValueChange={setTone}>
                      <SelectTrigger className="w-[180px] tone-button" data-testid="tone-selector">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="formal" data-testid="tone-formal">Formal</SelectItem>
                        <SelectItem value="conversational" data-testid="tone-conversational">Conversational</SelectItem>
                        <SelectItem value="academic" data-testid="tone-academic">Academic</SelectItem>
                        <SelectItem value="creative" data-testid="tone-creative">Creative</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Input Section */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700" data-testid="input-label">Original Text</label>
                    <span className="text-xs text-gray-500" data-testid="input-stats">
                      {inputWordCount} words, {inputCharCount} chars
                    </span>
                  </div>
                  <Textarea
                    data-testid="input-textarea"
                    placeholder="Paste or type your text here..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    className="min-h-[200px] text-base resize-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 flex-wrap">
                  <Button
                    data-testid="rephrase-button"
                    onClick={handleRephrase}
                    disabled={loading || !inputText.trim()}
                    className="action-button bg-teal-600 hover:bg-teal-700 text-white flex-1 min-w-[120px]"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 loading-spinner" />
                        Rephrasing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" />
                        Rephrase
                      </>
                    )}
                  </Button>
                  <Button
                    data-testid="clear-button"
                    onClick={handleClear}
                    variant="outline"
                    className="action-button"
                  >
                    <Eraser className="w-4 h-4 mr-2" />
                    Clear
                  </Button>
                </div>

                {/* Output Section */}
                {outputText && (
                  <div className="space-y-2 fade-in">
                    <Separator className="my-4" />
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-gray-700" data-testid="output-label">Rephrased Text</label>
                      <span className="text-xs text-gray-500" data-testid="output-stats">
                        {stats.words} words, {stats.chars} chars
                      </span>
                    </div>
                    <div className="bg-gradient-to-br from-teal-50 to-cyan-50 p-6 rounded-lg border border-teal-200">
                      <p className="text-base text-gray-800 leading-relaxed whitespace-pre-wrap" data-testid="output-text">
                        {outputText}
                      </p>
                    </div>
                    <Button
                      data-testid="copy-button"
                      onClick={handleCopy}
                      variant="outline"
                      className="action-button w-full mt-2"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy to Clipboard
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* History Sidebar */}
          <div className="lg:col-span-1">
            <Card className="glass-effect border-0 shadow-xl h-full" data-testid="history-card">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-2" data-testid="history-title">
                  <History className="w-5 h-5 text-teal-600" />
                  History
                </CardTitle>
                <CardDescription data-testid="history-description">{history.length} rephrasing{history.length !== 1 ? 's' : ''}</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  {history.length === 0 ? (
                    <div className="text-center py-12" data-testid="history-empty">
                      <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                      <p className="text-sm text-gray-500">No history yet</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div
                          key={item.id}
                          className="history-item p-4 rounded-lg border border-gray-200 bg-white cursor-pointer"
                          data-testid={`history-item-${item.id}`}
                        >
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <span className="text-xs font-medium text-teal-600 uppercase" data-testid={`history-tone-${item.id}`}>
                              {item.tone}
                            </span>
                            <Button
                              data-testid={`history-delete-${item.id}`}
                              variant="ghost"
                              size="sm"
                              onClick={() => deleteHistoryItem(item.id)}
                              className="h-6 w-6 p-0 hover:bg-red-50 hover:text-red-600"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                          <p
                            className="text-sm text-gray-700 line-clamp-2 mb-2"
                            onClick={() => loadHistoryItem(item)}
                            data-testid={`history-text-${item.id}`}
                          >
                            {item.original_text}
                          </p>
                          <span className="text-xs text-gray-400" data-testid={`history-date-${item.id}`}>
                            {new Date(item.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;